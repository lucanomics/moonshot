import json
import os
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup_event():
    global _pool
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    _pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
    print("[Moonshot] PostgreSQL 연결 풀 초기화 완료")


@app.on_event("shutdown")
async def shutdown_event():
    global _pool
    if _pool:
        await _pool.close()
        print("[Moonshot] PostgreSQL 연결 풀 종료")


@app.get("/api/visas")
async def get_visas():
    if not _pool:
        raise HTTPException(status_code=503, detail="DB 연결이 초기화되지 않았습니다.")
    async with _pool.acquire() as conn:
        visa_rows = await conn.fetch(
            "SELECT code, name, cat, period, new_req, ext_req, faq, "
            "data_badge, data_date, aliases FROM visas ORDER BY sort_order"
        )
        sub_rows = await conn.fetch(
            "SELECT code, parent_code, name, add_req, note, aliases "
            "FROM visa_sub_codes ORDER BY parent_code, sort_order"
        )

    sub_map: dict = {}
    for s in sub_rows:
        parent = s["parent_code"]
        sub_map.setdefault(parent, []).append({
            "code": s["code"],
            "name": s["name"],
            "addReq": s["add_req"],
            "note": s["note"],
            **(({"aliases": json.loads(s["aliases"])} if s["aliases"] else {})),
        })

    result = []
    for v in visa_rows:
        entry = {
            "code": v["code"],
            "name": v["name"],
            "cat": v["cat"],
            "period": v["period"],
            "newReq": v["new_req"],
            "extReq": v["ext_req"],
            "faq": v["faq"],
        }
        if v["data_badge"]:
            entry["dataBadge"] = v["data_badge"]
        if v["data_date"]:
            entry["dataDate"] = v["data_date"]
        if v["aliases"]:
            entry["aliases"] = json.loads(v["aliases"])
        subs = sub_map.get(v["code"])
        if subs:
            entry["subCodes"] = subs
        result.append(entry)

    return result


LOGS_FILE = Path("logs.json")


def classify_category(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["비자", "visa", "사증"]):
        return "비자문의"
    if any(k in q for k in ["체류", "연장", "등록"]):
        return "체류문의"
    return "기타"


def append_log(category: str, success: bool):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "category": category,
        "success": success,
    }
    logs = []
    if LOGS_FILE.exists():
        try:
            logs = json.loads(LOGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []
    logs.append(entry)
    LOGS_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/logs")
def get_logs():
    if not LOGS_FILE.exists():
        return []
    try:
        return json.loads(LOGS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def search_law(query: str) -> str:
    key = os.getenv("LAW_API_KEY")
    if not key:
        return ""
    url = "http://apis.data.go.kr/1170000/law/lawSearchList.do"
    params = {
        "serviceKey": key,
        "query": query,
        "display": 3,
        "numOfRows": 3,
        "type": "JSON",
    }
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params, timeout=10)
            data = res.json()
            laws = data.get("LawSearch", {}).get("law", [])
            if not laws:
                return ""
            return "\n".join(
                f"[{l.get('법령명한글', '')}] {l.get('법령약칭명', '')}" for l in laws
            )
    except Exception:
        return ""


class AskRequest(BaseModel):
    question: str
    context: str = ""
    consent: bool = True


@app.post("/api/ask")
async def ask(req: AskRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    if not req.question.strip():
        return {"answer": "질문을 입력해주세요."}

    category = classify_category(req.question)
    law_context = await search_law(req.question)

    system_prompt = (
        "당신은 제주출입국·외국인청 민원 안내 AI입니다.\n"
        "한국 비자, 체류, 출입국 관련 질문에 한국어와 영어로 답변합니다.\n"
        "사용자가 문법이 틀리거나 질문이 불완전해도 의도를 최대한 파악해서 친절하게 답변하세요.\n"
        "예: '비자 어떻게?' → 어떤 비자를 물어보는지 맥락으로 추론해서 답변.\n"
        "답변은 간결하게, 핵심만, 마지막에 '정확한 사항은 공식 창구에서 확인하세요' 안내 추가."
    )
    if law_context:
        system_prompt += f"\n\n관련 법령:\n{law_context}"
    if req.context:
        system_prompt += f"\n\n참고 비자 정보:\n{req.context}"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.question},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if req.consent:
                append_log(category, success=False)
            raise HTTPException(status_code=502, detail=f"Groq API 오류: {e.response.text}")
        except httpx.RequestError as e:
            if req.consent:
                append_log(category, success=False)
            raise HTTPException(status_code=502, detail=f"Groq API 연결 오류: {str(e)}")

    result = resp.json()
    answer = result["choices"][0]["message"]["content"]
    if req.consent:
        append_log(category, success=True)
    return {"answer": answer}


app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/ai")
@app.get("/ai.html")
async def read_ai():
    return FileResponse("ai.html")


@app.get("/")
@app.get("/index.html")
async def read_index():
    return FileResponse("index.html")
