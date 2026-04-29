from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

import os, re, json, logging, httpx, asyncpg
import xml.etree.ElementTree as ET
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

PUBLIC_DATA_KEY = "1673ea6ebbafabcb7d1bc2a9bbab40ed1444fb61a84d85ea8d839ea09d76d031"
cached_public_visa_data = "DATA MISSING"
cached_public_job_data  = "DATA MISSING"

# /api/ask 기본 폴백 체인
ASK_MODELS = [
    ("google/gemma-4-26b-a4b-it:free", "openrouter"),
    ("moonshotai/kimi-k2:free",         "openrouter"),
    ("llama-3.3-70b-versatile",         "groq"),
]

# /api/jobcodekeywords 폴백 체인
KEYWORD_MODELS = [
    ("llama-3.3-70b-versatile",         "groq"),
    ("llama-3.1-8b-instant",            "groq"),
    ("google/gemma-4-26b-a4b-it:free", "openrouter"),
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

async def init_public_data_cache():
    global cached_public_visa_data, cached_public_job_data
    logger.info("공공데이터 API(법무부, 국가데이터처) 초기 캐싱을 시작한다.")
    odcloud_base = "https://api.odcloud.kr/api"
    params = {"serviceKey": PUBLIC_DATA_KEY, "perPage": 50, "returnType": "JSON"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res_visa = await client.get(f"{odcloud_base}/15103561/v1/uddi:15103561", params=params)
            if res_visa.status_code == 200:
                data = res_visa.json().get("data", [])
                cached_public_visa_data = json.dumps(data[:10], ensure_ascii=False) if data else "DATA MISSING"
            else:
                logger.warning(f"체류자격 API HTTP 오류: {res_visa.status_code}")
        except Exception as e:
            logger.error(f"체류자격 공공데이터 패치 실패: {e}")

        try:
            res_job = await client.get(f"{odcloud_base}/15117819/v1/uddi:15117819", params=params)
            if res_job.status_code == 200:
                data = res_job.json().get("data", [])
                cached_public_job_data = json.dumps(data[:10], ensure_ascii=False) if data else "DATA MISSING"
            else:
                logger.warning(f"산업직업분류 API HTTP 오류: {res_job.status_code}")
        except Exception as e:
            logger.error(f"산업직업분류 공공데이터 패치 실패: {e}")

async def fetch_realtime_law_data(query: str) -> str:
    triggers = ["법", "벌금", "불법", "퇴거", "위반", "체류", "연장", "사증", "비자", "출입국"]
    if not any(t in query for t in triggers):
        return "DATA MISSING"

    url = "https://apis.data.go.kr/1170000/law"
    params = {
        "serviceKey": PUBLIC_DATA_KEY,
        "target": "law",
        "type": "XML",
        "query": "출입국관리법",
        "display": 3,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return "DATA MISSING"
            root = ET.fromstring(res.text)
            extracted_laws = []
            for item in root.findall(".//law"):
                title = item.findtext("법령명", default="")
                extracted_laws.append(f"[{title}] 출입국관리법령 검색 됨 (엄격 적용 요망)")
            return " | ".join(extracted_laws) if extracted_laws else "DATA MISSING"
    except Exception as e:
        logger.error(f"국가법령정보 실시간 조회 실패: {e}")
        return "DATA MISSING"

@app.on_event("startup")
async def startup_event():
    global db_pool
    await init_public_data_cache()
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

def select_models_by_lang(lang: str, question: str) -> list:
    complex_kw = ["동시에", "변경 후", "갱신하면서", "예외", "처벌", "취소", "강제퇴거",
                  "이의신청", "행정심판", "이중", "불법", "퇴거", "조건", "가능한가"]
    is_complex = any(kw in question for kw in complex_kw) or len(question) > 80

    # 중국어: Kimi가 가장 적합
    if lang == "zh":
        return [
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
    # 한국어/일본어 복잡 질문: 고성능 모델 우선
    elif lang in ("ko", "ja") and is_complex:
        return [
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
    # 한국어/일본어 단순 질문
    elif lang in ("ko", "ja"):
        return [
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
    # 기타 언어
    else:
        return ASK_MODELS

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
            return JSONResponse(status_code=200, content={"data": []})
    except Exception as e:
        logger.error(f"/api/visas DB 쿼리 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 쿼리 중 오류가 발생했습니다.")

@app.post("/api/jobcodekeywords")
async def extract_jobcodekeywords(req: KeywordRequest):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    groq_key       = os.environ.get("GROQ_API_KEY", "")

    if not openrouter_key and not groq_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY 또는 GROQ_API_KEY가 설정되지 않았습니다.")

    system_prompt = (
        "당신은 대한민국 통계청 '한국표준직업분류(KSCO)' 및 '한국표준산업분류(KSIC)' 데이터베이스 검색을 위한 형태소/어근 추출 전문가이다.\n"
        "사용자가 모호한 일상어를 입력할 때 프론트엔드 검색 명중률을 극대화하도록 가장 짧고 포괄적인 '핵심 명사(어근)'를 각각 5개씩 반드시 추출하라.\n\n"
        "[절대 원칙]\n"
        "1. 직업/직무: 행위 중심 명사 (정답 예시: '조리', '주방', '서빙', '계산', '건설')\n"
        "2. 산업/업종: 장소/분야 중심 명사 (정답 예시: '음식', '중식', '식당', '소매', '건축')\n"
        "출력은 마크다운 기호가 일절 포함되지 않은 순수 JSON 객체여야 한다:\n"
        '{"jobkeywords": ["kw1","kw2","kw3","kw4","kw5"], "industrykeywords": ["kw1","kw2","kw3","kw4","kw5"]}'
    )

    for model, provider in KEYWORD_MODELS:
        if provider == "openrouter" and not openrouter_key: continue
        if provider == "groq" and not groq_key: continue

        config  = _get_provider_config(provider, openrouter_key, groq_key)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.query},
            ],
            "max_tokens": 300,
            "temperature": 0.0,
        }
        if "gemma" not in model:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(config["url"], headers=config["headers"], json=payload)
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"]
                json_match = re.search(r"\{.*\}", answer, flags=re.DOTALL)
                if not json_match:
                    raise ValueError("JSON 파싱 실패")
                parsed = json.loads(json_match.group(0))
                return {
                    "job_keywords":      parsed.get("jobkeywords")      or parsed.get("job_keywords",      []),
                    "industry_keywords": parsed.get("industrykeywords") or parsed.get("industry_keywords", []),
                }
        except Exception as e:
            logger.error(f"[{provider}/{model}] 추출 실패: {e}")
            continue

    raise HTTPException(status_code=503, detail="AI 응답 지연 또는 파싱 실패. DATA MISSING.")

@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    groq_key       = os.environ.get("GROQ_API_KEY", "")

    if not openrouter_key and not groq_key:
        raise HTTPException(status_code=500, detail="API 키 미설정 상태.")

    category = classify_category(req.question)

    try:
        user_lang = detect(req.question)
    except Exception:
        user_lang = "ko"

    realtime_law_context = await fetch_realtime_law_data(req.question)

    system_prompt = f"""You are an elite, strict, and highly objective Korean immigration law assistant 2026 Manual Standard. 
Answer in the user's language ({user_lang}), but accurately translate and retain Korean legal terms. 
Always base your answer strictly on the 2026 Korean Immigration Act and the provided contexts below. 
CRITICAL RULES:
1. DO NOT hallucinate or guess. If exact answers are not found in the provided contexts, you MUST state "DATA MISSING" and refuse to answer.
2. Do not provide unwarranted sympathy or conversational filler.
3. If a request is legally impossible based on the context, state it firmly.

[Provided Context]
- RAG: {cached_public_visa_data}
- RAG: {cached_public_job_data}
- RAG: {realtime_law_context}

[프론트엔드 제공 컨텍스트]:
{req.context if req.context else "DATA MISSING"}

[공공데이터(RAG) - 법무부 체류자격 코드 캐시]:
{cached_public_visa_data}

[공공데이터(RAG) - 통계청 산업/직업분류 캐시]:
{cached_public_job_data}

[국가법령정보공유서비스 - 출입국관리법 실시간 조회]:
{realtime_law_context}
"""

    dynamic_models = select_models_by_lang(user_lang, req.question)

    for model_name, provider in dynamic_models:
        if provider == "openrouter" and not openrouter_key: continue
        if provider == "groq" and not groq_key: continue

        config  = _get_provider_config(provider, openrouter_key, groq_key)
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.question},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(config["url"], headers=config["headers"], json=payload)
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"]
                append_log(category, success=True)
                return {
                    "answer":        answer,
                    "model":         model_name,
                    "provider":      provider,
                    "lang_detected": user_lang,
                }
        except Exception as e:
            logger.error(f"[{provider}/{model_name}] 호출 실패: {e}")
            continue

    append_log(category, success=False)
    raise HTTPException(status_code=503, detail="현재 AI 트래픽 폭주. 잠시 후 재시도할 것.")

@app.get("/")
@app.get("/index.html")
async def serve_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="DATA MISSING: index.html")

@app.get("/ai.html")
async def serve_ai():
    if os.path.exists("ai.html"):
        return FileResponse("ai.html")
    raise HTTPException(status_code=404, detail="DATA MISSING: ai.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
