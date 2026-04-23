from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

import os, re, json, logging, httpx, asyncpg
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

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

db_pool = None
LOGS_FILE = Path("logs.json")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_API_URL       = "https://api.groq.com/openai/v1/chat/completions"
SITE_URL   = os.environ.get("SITE_URL", "https://web-production-14f9a.up.railway.app")
SITE_TITLE = "Moonshot Immigration AI"

# /api/ask 용 모델 폴백 체인
ASK_MODELS = [
    ("moonshotai/kimi-k2",            "openrouter"),  # 1순위
    ("moonshotai/kimi-k2:free",       "openrouter"),  # 2순위 (무료)
    ("google/gemma-3-27b-it:free",    "openrouter"),  # 3순위 (무료)
    ("llama-3.3-70b-versatile",       "groq"),        # 4순위
    ("gemma2-9b-it",                  "groq"),        # 5순위 (최후 수단)
]

# /api/jobcodekeywords 용 모델 폴백 체인
KEYWORD_MODELS = [
    ("moonshotai/kimi-k2",            "openrouter"),  # 1순위
    ("moonshotai/kimi-k2:free",       "openrouter"),  # 2순위 (무료)
    ("google/gemma-3-27b-it:free",    "openrouter"),  # 3순위 (무료)
    ("llama-3.3-70b-versatile",       "groq"),        # 4순위
]


def _get_provider_config(provider: str, openrouter_key: str, groq_key: str) -> dict:
    if provider == "openrouter":
        return {
            "url": OPENROUTER_API_URL,
            "headers": {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_TITLE,
            },
        }
    elif provider == "groq":
        return {
            "url": GROQ_API_URL,
            "headers": {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
        }
    else:
        raise ValueError(f"알 수 없는 provider: {provider}")


@app.on_event("startup")
async def startup_event():
    global db_pool
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL 미설정 — DB 기능 비활성화, JSON 폴백 모드로 실행")
        return
    try:
        db_pool = await asyncpg.create_pool(db_url)
        logger.info("PostgreSQL 비동기 커넥션 풀 적재 완료.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("DB 연결 실패 — JSON 폴백 모드로 실행")


@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
        logger.info("PostgreSQL 커넥션 풀 종료.")


class AskRequest(BaseModel):
    question: str
    consent: bool
    context: Optional[str] = ""
    lang: Optional[str] = "ko"


class KeywordRequest(BaseModel):
    query: str


def classify_category(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["유학", "d-2", "학생", "대학교", "어학연수", "d-4"]): return "study"
    if any(w in q for w in ["취업", "일", "알바", "e-", "e-7", "e-9", "직장", "h-2"]): return "work"
    if any(w in q for w in ["결혼", "가족", "배우자", "f-6", "f-3", "f-1", "부모"]): return "family"
    if any(w in q for w in ["투자", "사업", "법인", "d-8", "d-9"]): return "invest"
    if any(w in q for w in ["건강보험", "건보", "보험료"]): return "nhis"
    if any(w in q for w in ["영주권", "국적", "f-5", "귀화"]): return "permanent"
    return "general"


def append_log(category: str, success: bool):
    try:
        logs = []
        if LOGS_FILE.exists():
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        logs.append({"timestamp": datetime.now().isoformat(), "category": category, "success": success})
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"로그 기록 실패: {e}")


@app.get("/api/visas")
async def get_visas():
    if not db_pool:
        return JSONResponse(status_code=200, content={"data": []})
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT data FROM visas_json LIMIT 1")
            if rows:
                return JSONResponse(content=json.loads(rows[0]["data"]))
            else:
                return JSONResponse(status_code=200, content={"data": []})
    except Exception as e:
        logger.error(f"/api/visas DB 쿼리 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 쿼리 중 오류가 발생했습니다.")


@app.post("/api/jobcodekeywords")
async def extract_jobcode_keywords(req: KeywordRequest):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    groq_key       = os.environ.get("GROQ_API_KEY", "")

    if not openrouter_key and not groq_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY 또는 GROQ_API_KEY가 설정되지 않았습니다.")

    system_prompt = (
        "당신은 대한민국 통계청 '한국표준직업분류(KSCO)' 및 '한국표준산업분류(KSIC)' 데이터베이스 검색을 위한 형태소/어근 추출 전문가입니다.\n"
        "사용자가 '중식당 배달', '노가다', '편의점 알바' 등 모호한 일상어를 입력할 때, 프론트엔드의 단순 텍스트 포함(includes) 검색에서 명중률(Hit Rate)이 극대화되도록 가장 짧고 포괄적인 '핵심 명사(어근)'를 각각 5개씩 반드시 추출하십시오.\n\n"
        "[분리 및 추출 절대 원칙]\n"
        "1. jobkeywords (직업/직무 - 무엇을 하는가?): '서비스업', '판매종사자'처럼 길게 쓰지 마십시오. -> (정답 예시: '조리', '주방', '서빙', '접객', '계산', '판매', '노무', '건설')\n"
        "2. industrykeywords (산업/업종 - 어디서 일하는가?): '음식점업', '소매업'처럼 길게 쓰지 마십시오. -> (정답 예시: '음식', '중식', '외식', '식당', '소매', '편의', '상점', '건축')\n\n"
        "절대 빈 배열을 반환하지 마십시오. 입력값이 아무리 짧아도 가장 확률이 높은 단어로 유추하여 무조건 5개를 꽉 채우십시오.\n"
        "출력은 마크다운 기호가 일절 포함되지 않은 순수 JSON 객체여야 합니다:\n"
        '{"jobkeywords": ["kw1","kw2","kw3","kw4","kw5"], "industrykeywords": ["kw1","kw2","kw3","kw4","kw5"]}'
    )

    for model, provider in KEYWORD_MODELS:
        if provider == "openrouter" and not openrouter_key:
            logger.warning(f"[{model}] OPENROUTER_API_KEY 없음 — 건너뜀")
            continue
        if provider == "groq" and not groq_key:
            logger.warning(f"[{model}] GROQ_API_KEY 없음 — 건너뜀")
            continue

        config = _get_provider_config(provider, openrouter_key, groq_key)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.query},
            ],
            "max_tokens": 300,
            "temperature": 0.1,
        }
        # gemma 계열은 response_format json_object 미지원 → 조건부 적용
        if "gemma" not in model:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(config["url"], headers=config["headers"], json=payload)
                resp.raise_for_status()
                data   = resp.json()
                answer = data["choices"][0]["message"]["content"]

                json_match = re.search(r"\{.*\}", answer, flags=re.DOTALL)
                if not json_match:
                    raise ValueError("JSON 객체를 파싱할 수 없습니다.")

                parsed = json.loads(json_match.group(0))
                result = {
                    "jobkeywords":      parsed.get("jobkeywords")      or parsed.get("job_keywords",      []),
                    "industrykeywords": parsed.get("industrykeywords") or parsed.get("industry_keywords", []),
                }

                logger.info(f"[jobcodekeywords] 성공 — provider={provider}, model={model}")
                return result

        except Exception as e:
            logger.error(f"[{provider}/{model}] 직종 키워드 추출 실패: {e}")
            continue

    raise HTTPException(status_code=503, detail="AI 모델 응답 지연 또는 JSON 파싱 실패로 키워드를 추출할 수 없습니다.")


@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    groq_key       = os.environ.get("GROQ_API_KEY", "")

    if not openrouter_key and not groq_key:
        raise HTTPException(status_code=500, detail="서버 구성 오류: API 키가 설정되지 않았습니다.")

    category = classify_category(req.question)

    try:
        user_lang = detect(req.question)
    except Exception:
        user_lang = "ko"

    system_prompt = f"""You are an elite Korean immigration law assistant.
The user's query language appears to be '{user_lang}'.
If it is not Korean, answer in the user's language, but accurately translate and explain the Korean legal terms.
Always base your answer on the 2026 Korean Immigration Act and Visa Manuals.
Be direct, objective, and precise. DO NOT hallucinate. Do not use markdown blocks unless necessary.
Context: {req.context}"""

    for model_name, provider in ASK_MODELS:
        if provider == "openrouter" and not openrouter_key:
            logger.warning(f"[{model_name}] OPENROUTER_API_KEY 없음 — 건너뜀")
            continue
        if provider == "groq" and not groq_key:
            logger.warning(f"[{model_name}] GROQ_API_KEY 없음 — 건너뜀")
            continue

        config = _get_provider_config(provider, openrouter_key, groq_key)
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.question},
            ],
            "max_tokens": 2048,
            "temperature": 0.4,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(config["url"], headers=config["headers"], json=payload)
                resp.raise_for_status()
                data   = resp.json()
                answer = data["choices"][0]["message"]["content"]
                logger.info(f"[ask] 성공 — provider={provider}, model={model_name}")
                append_log(category, success=True)
                return {"answer": answer}

        except Exception as e:
            logger.error(f"[{provider}/{model_name}] 호출 실패: {e}")
            continue

    append_log(category, success=False)
    raise HTTPException(status_code=503, detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.")


@app.get("/")
@app.get("/index.html")
async def serve_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="index.html 파일을 찾을 수 없습니다.")


@app.get("/ai.html")
async def serve_ai():
    if os.path.exists("ai.html"):
        return FileResponse("ai.html")
    raise HTTPException(status_code=404, detail="ai.html 파일을 찾을 수 없습니다.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
