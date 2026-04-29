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

# ✅ 환경변수로 교체 (보안)
PUBLIC_DATA_KEY = os.environ.get("LAW_API_KEY", "")
cached_public_visa_data = "DATA MISSING"
cached_public_job_data  = "DATA MISSING"

# --- 매뉴얼 RAG (Supabase pgvector) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = (
    os.environ.get("SUPABASE_SERVICE_KEY", "")
    or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
)
# ✅ RAG 임베딩 → OpenRouter (text-embedding-3-small)
RAG_EMBED_MODEL = "openai/text-embedding-3-small"
RAG_EMBED_URL   = "https://openrouter.ai/api/v1/embeddings"
RAG_TOP_K = 4

# /api/ask 용 모델 폴백 체인
ASK_MODELS = [
    ("moonshotai/kimi-k2:free",         "openrouter"),
    ("google/gemma-4-26b-a4b-it:free", "openrouter"),  
    ("llama-3.3-70b-versatile",       "groq"),            
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
    visa_data: Optional[dict] = None

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

    if lang == "zh":
        return [
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
    elif lang in ("ko", "ja") and is_complex:
        return [
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
    elif lang in ("ko", "ja"):
        return [
            ("google/gemma-4-26b-a4b-it:free", "openrouter"),
            ("moonshotai/kimi-k2:free",         "openrouter"),
            ("llama-3.3-70b-versatile",         "groq"),
        ]
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

DISCLAIMER_SUFFIX = (
    "⚠ 본 답변은 2026년 4월 법무부 출입국 실무 매뉴얼 기준이며, "
    "개인 상황에 따라 달라질 수 있습니다. 최종 확인은 반드시 ☎ 1345 또는 "
    "관할 출입국·외국인관서에서 하십시오."
)

ANTI_HALLUCINATION_INSTRUCTION = (
    "[답변 생성 지침]\n"
    "- 위 [참고 자료]에 명시된 내용만 인용하십시오.\n"
    "- [참고 자료]에 없는 내용을 질문받으면: \"해당 사항은 제공된 자료에 명시되어 있지 않습니다. ☎ 1345로 직접 문의하십시오.\"라고만 답하십시오.\n"
    "- 수치(금액, 기간, 점수, 비율)가 포함된 답변은 반드시 출처 문장(예: \"매뉴얼 [신규 요건] 항목에 따르면\")을 함께 명시하십시오.\n"
)


async def _embed_query(text: str) -> Optional[list]:
    """OpenRouter로 text-embedding-3-small 쿼리 임베딩.
    환경변수 미설정 또는 호출 실패 시 None 반환 (graceful degradation)."""
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not openrouter_key or not text.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                RAG_EMBED_URL,
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": SITE_URL,
                    "X-Title": SITE_TITLE,
                },
                json={"model": RAG_EMBED_MODEL, "input": text[:2000]},
            )
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]
    except Exception as e:
        logger.warning(f"RAG 임베딩 실패: {e}")
        return None


async def retrieve_manual_context(question: str, visa_code: Optional[str], top_k: int = RAG_TOP_K) -> str:
    """Supabase pgvector RPC로 매뉴얼 청크 유사도 검색.
    - SUPABASE_URL/KEY 미설정, 임베딩 실패, RPC 오류 시 빈 문자열 반환.
    - visa_code 가 주어지면 해당 코드 청크만 우선 검색, 결과가 비면 전체 검색으로 fallback.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return ""
    embedding = await _embed_query(question)
    if embedding is None:
        return ""

    rpc_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/rpc/match_manual_chunks"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }

    async def _call(filter_code: Optional[str]) -> list:
        payload = {
            "query_embedding": embedding,
            "match_count": top_k,
            "filter_visa_code": filter_code,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(rpc_url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json() or []
        except Exception as e:
            logger.warning(f"RAG RPC 실패(filter={filter_code}): {e}")
            return []

    rows = await _call(visa_code) if visa_code else []
    if not rows:
        rows = await _call(None)
    if not rows:
        return ""

    snippets = []
    for i, row in enumerate(rows, 1):
        src = row.get("source", "?")
        page = row.get("page_num")
        code = row.get("visa_code") or "공통"
        head = f"[매뉴얼 발췌 {i} | {src} p.{page} | {code}]"
        snippets.append(f"{head}\n{row.get('content', '')}")
    return "\n\n".join(snippets)


def _build_visa_block(visa_data: Optional[dict]) -> str:
    if not visa_data:
        return ""
    v = visa_data
    return (
        "[참고 자료 — 2026년 4월 법무부 출입국 실무 매뉴얼]\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"체류자격 코드: {v.get('code') or '미상'}\n"
        f"체류자격 명칭: {v.get('name') or '미상'}\n"
        f"기본 체류기간: {v.get('period') or '미상'}\n"
        f"카테고리: {v.get('cat') or '미상'}\n\n"
        "[신규 발급 요건]\n"
        f"{v.get('newReq') or '정보 없음'}\n\n"
        "[체류기간 연장 요건]\n"
        f"{v.get('extReq') or '정보 없음'}\n\n"
        "[FAQ / 실무 주의사항]\n"
        f"{v.get('faq') or '정보 없음'}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )


@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    if not req.consent:
        raise HTTPException(status_code=400, detail="동의가 필요합니다.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해 주세요.")

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

    # 언어별 답변 지침 분기
    if user_lang == "ko":
        lang_instruction = (
            "5. 답변은 반드시 한국어로만 작성하십시오. "
            "일본어(ただし, また 등), 영어, 중국어 등 다른 언어의 단어를 절대 섞지 마십시오. "
            "번호 목록 형식으로 명확하게 작성하십시오.\n"
        )
    else:
        lang_instruction = (
            f"5. 답변은 사용자 언어({user_lang})로 작성하되, "
            "한국 법률 용어는 정확히 한국어 원어를 함께 표기하고, "
            "하나의 답변 안에서 다른 언어를 무분별하게 혼용하지 마십시오. "
            "번호 목록 형식으로 명확하게 작성하십시오.\n"
        )

    system_prompt = (
        "당신은 대한민국 법무부 출입국·외국인정책본부의 2026년 4월 최신 실무 매뉴얼"
        "(사증민원·체류민원)에 정통한 비자 상담 전문가입니다.\n\n"
        "[절대 규칙 — 반드시 준수]\n"
        "1. 반드시 아래 [참고 자료]에 명시된 내용만을 근거로 답변하십시오.\n"
        "2. [참고 자료]에 없는 수치(금액, 기간, 점수, 비율), 요건, 서류명은 절대로 생성하지 마십시오.\n"
        "3. 확인할 수 없는 사항은 반드시 \"매뉴얼에 명시되지 않은 사항입니다.\"라고 명확히 밝히십시오.\n"
        "4. 추측, 유추, 일반 상식으로 빈칸을 채우지 마십시오.\n"
        f"{lang_instruction}"
        "6. 출입국관리사무소 예약 여부, 동시 신청 가능 여부 등 운영 정책은 관할 사무소마다 다를 수 있으므로 확정적으로 서술하지 마십시오.\n"
        "7. 근거 없는 절차 안내(예: '방문하여 신청하시면 됩니다')를 단독으로 제시하지 마십시오.\n"
        f"8. 모든 답변 마지막에 반드시 다음 면책 고지를 그대로 추가하십시오:\n   \"{DISCLAIMER_SUFFIX}\"\n\n"
        "[보조 컨텍스트 (RAG 캐시)]\n"
        f"- 법무부 체류자격 코드 캐시: {cached_public_visa_data}\n"
        f"- 통계청 산업/직업분류 캐시: {cached_public_job_data}\n"
        f"- 국가법령정보공유서비스(출입국관리법) 실시간 조회: {realtime_law_context}\n"
    )

    visa_block = _build_visa_block(req.visa_data)
    extra_context = req.context.strip() if req.context else ""

    rag_visa_code = req.visa_data.get("code") if req.visa_data else None
    rag_block = await retrieve_manual_context(req.question, rag_visa_code)

    user_prompt_parts = []
    if rag_block:
        user_prompt_parts.append(
            "[참고 자료 — 법무부 매뉴얼 벡터 검색 결과]\n" + rag_block
        )
    if visa_block:
        user_prompt_parts.append(visa_block)
    if extra_context:
        user_prompt_parts.append(f"[프론트엔드 제공 컨텍스트]\n{extra_context}")
    user_prompt_parts.append(f"[민원인 질문]\n{req.question}")
    user_prompt_parts.append(ANTI_HALLUCINATION_INSTRUCTION)
    user_prompt = "\n\n".join(user_prompt_parts)

    dynamic_models = select_models_by_lang(user_lang, req.question)

    for model_name, provider in dynamic_models:
        if provider == "openrouter" and not openrouter_key: continue
        if provider == "groq" and not groq_key: continue

        config  = _get_provider_config(provider, openrouter_key, groq_key)
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.1,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(config["url"], headers=config["headers"], json=payload)
                resp.raise_for_status()
                data   = resp.json()
                answer = data["choices"][0]["message"]["content"]

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
