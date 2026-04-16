import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

load_dotenv()

app = FastAPI()

# CORS 설정 (프론트엔드 HTML에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 비자 데이터를 메모리에 캐시
_visa_cache: list = []

def load_visa_data() -> list:
    global _visa_cache
    if _visa_cache:
        return _visa_cache
    for filename in ["visa_data.json", "visa_data (1).json"]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                _visa_cache = json.load(f)
                print(f"[Moonshot] {filename}에서 {len(_visa_cache)}개의 비자 데이터를 로드했습니다.")
                return _visa_cache
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"[Moonshot] {filename} 로드 오류: {e}")
    print("[Moonshot] 경고: 비자 데이터 파일을 찾을 수 없습니다.")
    return []


@app.on_event("startup")
def startup_event():
    load_visa_data()


@app.get("/api/visas")
def get_visas():
    data = load_visa_data()
    if not data:
        raise HTTPException(status_code=500, detail="비자 데이터를 로드할 수 없습니다.")
    return data


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
            result = []
            for law in laws:
                result.append(f"[{law.get('법령명한글', '')}] {law.get('법령약칭명', '')}")
            return "\n".join(result)
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

    # 관련 법령 검색
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

    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
    if req.consent:
        append_log(category, success=True)
    return {"answer": answer}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 서버가 현재 폴더의 HTML 파일들을 직접 읽어서 보내주도록 설정
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.get("/ai.html")
async def read_ai():
    return FileResponse("ai.html")

@app.get("/admin.html")
async def read_admin():
    return FileResponse("admin.html")
