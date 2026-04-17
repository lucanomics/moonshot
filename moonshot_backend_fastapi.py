import os
import json
import logging
import httpx
import asyncpg
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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
        raise RuntimeError("DATABASE_URL is missing in environment variables.")
    try:
        db_pool = await asyncpg.create_pool(db_url)
        logger.info("PostgreSQL 비동기 커넥션 풀 적재 완료.")
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        await db_pool.close()

class AskRequest(BaseModel):
    question: str
    consent: bool
    context: Optional[str] = ""

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

# [추가됨] DB 기반 비자 정보 동적 검색 (Backend RAG Pipeline)
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
        raise HTTPException(status_code=500, detail="데이터베이스 연결이 초기화되지 않았습니다.")
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
            if not json_str: return {"data": [], "status": "empty"}
            return json.loads(json_str)
    except Exception as e:
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
    
    # 텅 빈 프론트엔드 컨텍스트를 대체할 백엔드 데이터 강제 추출
    db_context = await search_visa_db(req.question)

    # [수정됨] 절대 규칙 하드닝: 오버스테이 방어벽 구축
    system_prompt = (
        "당신은 대한민국 출입국·외국인청 소속의 최고위급 민원 안내 전문 AI 'Moonshot'이다.\n"
        "[절대 규칙]\n"
        "1. 철저히 건조하고 기계적이며 객관적인 문체(~이다, ~한다)만 사용할 것.\n"
        "2. 인사말, 사과, 감정적 표현, 친절한 수식어는 일절 배제할 것.\n"
        "3. 제공된 [참고 비자 정보]를 최우선으로 검토하여 답변할 것.\n"
        "4. 핵심 요건, 절차, 서류는 반드시 글머리 기호(-)를 사용하여 가독성 있게 구조화할 것.\n"
        "5. 체류기간 도과(오버스테이, 기한 초과, 불법체류) 정황이 질문에 포함된 경우, 일반 체류 연장 절차 안내를 전면 중단할 것.\n"
        "6. 위법 상태 체류자에게는 반드시 '출입국관리법 위반에 따른 범칙금 부과', '출국명령 또는 강제퇴거', '자진출국제도' 절차만을 단호하고 엄격하게 고지할 것."
    )
    if law_context:
        system_prompt += f"\n\n[관련 법령]:\n{law_context}"
    
    # 추출된 DB 컨텍스트 최우선 주입
    if db_context:
        system_prompt += f"\n\n[참고 비자 정보 (DB 검색 결과)]:\n{db_context}"
    elif req.context:
        system_prompt += f"\n\n[참고 비자 정보 (화면 전달)]:\n{req.context}"

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
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                append_log(category, success=True)
                return {"answer": answer}
        except Exception as e:
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
