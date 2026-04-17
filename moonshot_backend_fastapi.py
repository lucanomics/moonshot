import os
import asyncpg
import httpx
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MoonshotBackend")

app = FastAPI(title="Moonshot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_pool: Optional[asyncpg.Pool] = None
LOGS_FILE = Path("logs.json")


@app.on_event("startup")
async def startup_event():
    global _pool
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    logger.info("PostgreSQL 연결 풀 생성 완료.")


@app.on_event("shutdown")
async def shutdown_event():
    global _pool
    if _pool:
        await _pool.close()
        logger.info("PostgreSQL 연결 풀 종료.")


def _row_to_visa(row: dict, sub_rows: list) -> dict:
    """DB 행 → 기존 visa_data.json 구조로 조립"""
    v: dict = {
        "code": row["code"],
        "name": row["name"],
        "cat": row["cat"],
        "period": row["period"],
        "newReq": row["new_req"],
        "extReq": row["ext_req"],
        "faq": row["faq"],
    }
    if row["data_badge"]:
        v["dataBadge"] = row["data_badge"]
    if row["data_date"]:
        v["dataDate"] = row["data_date"]
    if row["aliases"] is not None:
        v["aliases"] = json.loads(row["aliases"])
    subs = []
    for s in sorted(sub_rows, key=lambda x: x["sort_order"]):
        sub = {
            "code": s["code"],
            "name": s["name"],
            "addReq": s["add_req"],
            "note": s["note"],
        }
        if s["aliases"]:
            sub["aliases"] = json.loads(s["aliases"])
        subs.append(sub)
    if subs:
        v["subCodes"] = subs
    return v


@app.get("/api/visas")
async def get_visas():
    if not _pool:
        raise HTTPException(status_code=503, detail="DB 연결 풀이 초기화되지 않았습니다.")
    async with _pool.acquire() as conn:
        visa_rows = await conn.fetch("SELECT * FROM visas ORDER BY sort_order")
        sub_rows = await conn.fetch("SELECT * FROM visa_sub_codes ORDER BY parent_code, sort_order")
    sub_map: dict = {}
    for s in sub_rows:
        sub_map.setdefault(s["parent_code"], []).append(dict(s))
    return [_row_to_visa(dict(v), sub_map.get(v["code"], [])) for v in visa_rows]


# ─── 법제처 OpenAPI ───────────────────────────────────────────
LAW_API_BASE = "https://www.law.go.kr/DRF"


async def search_law(query: str) -> str:
    law_api_key = os.environ.get("LAW_API_KEY")
    if not law_api_key:
        logger.warning("LAW_API_KEY 누락: 법령 실시간 검색이 생략됩니다.")
        return ""
    try:
        search_params = {
            "OC": law_api_key, "target": "law", "type": "JSON",
            "query": query, "display": 3, "sort": "lasc",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"{LAW_API_BASE}/lawSearch.do", params=search_params)
            resp.raise_for_status()
            laws = resp.json().get("LawSearch", {}).get("law", [])
        if not laws:
            return ""
        context_parts = []
        async with httpx.AsyncClient(timeout=8.0) as client:
            for law in laws[:3]:
                law_id = law.get("법령ID") or law.get("MST")
                law_name = law.get("법령명한글", "")
                if not law_id:
                    continue
                try:
                    art_resp = await client.get(
                        f"{LAW_API_BASE}/lawService.do",
                        params={"OC": law_api_key, "target": "law", "type": "JSON", "ID": law_id},
                    )
                    art_resp.raise_for_status()
                    articles = art_resp.json().get("법령", {}).get("조문", {}).get("조문단위", [])
                    if isinstance(articles, dict):
                        articles = [articles]
                    for art in articles:
                        content = art.get("조문내용", "") or ""
                        title = art.get("조문제목", "") or ""
                        if any(kw in content or kw in title for kw in query.split()):
                            context_parts.append(f"[{law_name}] {title}\n{content}")
                        if len(context_parts) >= 5:
                            break
                except Exception as e:
                    logger.warning(f"조문 조회 실패 ({law_name}): {e}")
                    continue
        return "\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"법제처 API 호출 오류: {e}")
        return ""


# ─── 로그 ────────────────────────────────────────────────────
def classify_category(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["비자", "visa", "사증"]):
        return "비자문의"
    if any(k in q for k in ["체류", "연장", "등록"]):
        return "체류문의"
    return "기타"


def append_log(category: str, success: bool):
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
             "category": category, "success": success}
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


# ─── AI 질의 ─────────────────────────────────────────────────
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
        "당신은 대한민국 출입국·외국인청 소속의 최고위급 민원 안내 전문 AI 'Moonshot'이다.\n"
        "[절대 규칙]\n"
        "1. 철저히 건조하고 기계적이며 객관적인 문체(~이다, ~한다)만 사용할 것.\n"
        "2. 인사말, 사과, 감정적 표현, 친절한 수식어는 일절 배제할 것.\n"
        "3. 제공된 [관련 법령] 및 [참고 비자 정보]에만 기반하여 답변하고, 정보가 없으면 '데이터 부족으로 추측할 수 없음'이라고 단호히 명시할 것.\n"
        "4. 핵심 요건, 절차, 서류는 반드시 글머리 기호(-)를 사용하여 가독성 있게 구조화할 것."
    )
    if law_context:
        system_prompt += f"\n\n[관련 법령 (법제처 OpenAPI 실시간 조회)]:\n{law_context}"
    if req.context:
        system_prompt += f"\n\n[참고 비자 정보]:\n{req.context}"

    models_to_try = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question},
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
            "top_p": 0.9,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers, json=payload,
                )
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"]
                if req.consent:
                    append_log(category, success=True)
                logger.info(f"AI 추론 성공 (모델: {model_name})")
                return {"answer": answer}
        except Exception as e:
            if req.consent:
                append_log(category, success=False)
            logger.warning(f"모델 [{model_name}] 실패: {e}. 다음 모델 시도.")
            continue

    raise HTTPException(status_code=503, detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.")


# ─── 정적 파일 서빙 ──────────────────────────────────────────
app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/ai")
@app.get("/ai.html")
async def serve_ai():
    return FileResponse("ai.html")


@app.get("/")
@app.get("/index.html")
async def serve_index():
    return FileResponse("index.html")
