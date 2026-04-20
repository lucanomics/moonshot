import os
import json
import logging
import httpx
import asyncpg
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
    global db_pool
    if db_pool:
        await db_pool.close()

class AskRequest(BaseModel):
    question: str
    consent: bool
    context: Optional[str] = ""
    lang: Optional[str] = "ko"  # ✏️ 변경 1: lang 필드 추가

def classify_category(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["비자", "visa", "사증"]): return "비자문의"
    if any(k in q for k in ["체류", "연장", "등록"]): return "체류문의"
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
            pass
    logs.append(entry)
    LOGS_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/health")
async def health_check():
    if not db_pool:
        return JSONResponse(status_code=200, content={"status": "ok", "db": "json fallback mode"})
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error(f"Health check DB 오류: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "db": "unreachable"})

@app.get("/api/logs")
def get_logs():
    if not LOGS_FILE.exists(): return []
    try:
        return json.loads(LOGS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def search_law(query: str) -> str:
    law_api_key = os.environ.get("LAW_API_KEY")
    if not law_api_key: return ""
    return ""

async def search_visa_db(query: str) -> str:
    if not db_pool: return ""
    sql = """
    SELECT code, name, period, new_req, ext_req, faq
    FROM visas
    WHERE $1 ILIKE '%' || code || '%' OR $1 ILIKE '%' || name || '%'
    LIMIT 2;
    """
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(sql, query)
            if not rows: return ""
            ctx = ""
            for r in rows:
                ctx += f"- 비자종류: {r['name']} ({r['code']})\n"
                ctx += f"- 체류기간: {r['period']}\n"
                ctx += f"- 신규/연장요건: {r['new_req']} / {r['ext_req']}\n"
                ctx += f"- FAQ: {r['faq']}\n\n"
            return ctx.strip()
    except Exception as e:
        logger.error(f"DB 검색 실패: {e}")
        return ""

@app.get("/api/visas")
async def get_visas():
    if not db_pool:
        for fname in ["visa_data.json", "visa_data (1).json"]:
            p = Path(fname)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else data.get("data", [])
        raise HTTPException(status_code=500, detail="데이터베이스 및 JSON 파일 모두 없음")

    query = """
    SELECT json_agg(
        json_strip_nulls(
            json_build_object(
                'code', v.code, 'name', v.name, 'cat', v.cat, 'period', v.period,
                'newReq', v.new_req, 'extReq', v.ext_req, 'faq', v.faq,
                'dataBadge', v.data_badge, 'dataDate', v.data_date, 'aliases', v.aliases,
                'subCodes', (
                    SELECT json_agg(json_strip_nulls(json_build_object(
                        'code', s.code, 'name', s.name, 'addReq', s.add_req, 'note', s.note, 'aliases', s.aliases
                    )) ORDER BY s.sort_order)
                    FROM visa_sub_codes s WHERE s.parent_code = v.code
                )
            )
        ) ORDER BY v.sort_order
    ) FROM visas v;
    """
    try:
        async with db_pool.acquire() as conn:
            json_str = await conn.fetchval(query)
            if not json_str:
                return []
            result = json.loads(json_str)
            if isinstance(result, list):
                if len(result) == 1 and isinstance(result[0], list):
                    return result[0]
                return result
            logger.warning(f"/api/visas: 예상치 못한 응답 형식 — {type(result)}")
            return []
    except Exception as e:
        logger.error(f"/api/visas DB 쿼리 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 쿼리 중 오류가 발생했습니다.")

@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    if not req.consent:
        raise HTTPException(status_code=400, detail="개인정보 처리 동의가 필요합니다.")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="서버 내부 오류: AI API 키 누락")

    category = classify_category(req.question)
    law_context = await search_law(req.question)
    db_context = await search_visa_db(req.question)

    lang_map = {
        "ko": "한국어", "en": "English", "zh": "中文", "ja": "日本語",
        "th": "ภาษาไทย", "ru": "Русский", "ar": "العربية", "id": "Bahasa Indonesia",
    }
    reply_lang = lang_map.get(req.lang or "ko", "the same language as the user's question")

    system_prompt = (
    f"CRITICAL: You MUST respond ONLY in {reply_lang}. "
    f"Even if all reference data below is in Korean, your answer must be written entirely in {reply_lang}. "
    "Violating this rule is not acceptable under any circumstances.\n\n"
    "You are 'Moonshot', a top-tier immigration and visa guidance AI for the Republic of Korea.\n"
    "[ABSOLUTE RULES]\n"
    f"1. ALWAYS reply in {reply_lang}. Match the language of the user's question exactly.\n"
    "2. Use a dry, mechanical, objective tone. No greetings, apologies, or emotional expressions.\n"
    "3. Prioritize the provided [Visa Reference Data] above all else when answering.\n"
    "4. Structure requirements, procedures, and documents using bullet points (-) for readability.\n"
    "5. If the question involves overstay or illegal residence, immediately STOP any extension guidance.\n"
    "6. For illegal overstay cases, strictly inform only: penalty fines under Immigration Act, deportation order or forced removal, and voluntary departure program."
)
    if law_context:
        system_prompt += f"\n\n[관련 법령]:\n{law_context}"
    if db_context:
        system_prompt += f"\n\n[Visa Reference Data (DB)]:\n{db_context}"
    elif req.context:
        system_prompt += f"\n\n[Visa Reference Data (client)]:\n{req.context}"

    models_to_try = ["llama-3.3-70b-versatile", "gemma2-9b-it"]
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
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                append_log(category, success=True)
                return {"answer": answer}
        except Exception as e:
            logger.error(f"[{model_name}] 호출 실패: {e}")
            continue
            
    append_log(category, success=False)
    raise HTTPException(status_code=503, detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.")

@app.get("/")
@app.get("/index.html")
async def serve_index():
    if os.path.exists("index.html"): return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="index.html 파일을 찾을 수 없습니다.")

@app.get("/ai")
@app.get("/ai.html")
async def serve_ai():
    if os.path.exists("ai.html"): return FileResponse("ai.html")
    raise HTTPException(status_code=404, detail="ai.html 파일을 찾을 수 없습니다.")
