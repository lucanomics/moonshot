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

# 환경 변수 강제 로드
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MoonshotBackend")

app = FastAPI(title="Moonshot API")

# 보안 통제: 허용된 메서드만 개방
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 비동기 DB 커넥션 풀
db_pool = None
LOGS_FILE = Path("logs.json")

@app.on_event("startup")
async def startup_event():
    global db_pool
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("치명적 오류: DATABASE_URL 환경 변수가 누락되었습니다.")
        raise RuntimeError("DATABASE_URL is missing in environment variables.")
    
    try:
        db_pool = await asyncpg.create_pool(db_url)
        logger.info("PostgreSQL 비동기 커넥션 풀 적재 완료.")
    except Exception as e:
        logger.error(f"DB 연결 실패: {e}")
        raise RuntimeError(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("PostgreSQL 커넥션 풀 해제 완료.")

# [보안 패치 1] consent 속성을 필수로 강제하여 동의 우회 원천 차단
class AskRequest(BaseModel):
    question: str
    consent: bool  # 기본값(=True) 제거. 무조건 입력받아야 함.
    context: Optional[str] = ""

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
    law_api_key = os.environ.get("LAW_API_KEY")
    if not law_api_key:
        return ""
    return ""

@app.get("/api/visas")
async def get_visas():
    if not db_pool:
        raise HTTPException(status_code=500, detail="데이터베이스 연결이 초기화되지 않았습니다.")
        
    query = """
    SELECT json_agg(
        json_strip_nulls(
            json_build_object(
                'code', v.code,
                'name', v.name,
                'cat', v.cat,
                'period', v.period,
                'newReq', v.new_req,
                'extReq', v.ext_req,
                'faq', v.faq,
                'dataBadge', v.data_badge,
                'dataDate', v.data_date,
                'aliases', v.aliases,
                'subCodes', (
                    SELECT json_agg(
                        json_strip_nulls(
                            json_build_object(
                                'code', s.code,
                                'name', s.name,
                                'addReq', s.add_req,
                                'note', s.note,
                                'aliases', s.aliases
                            )
                        ) ORDER BY s.sort_order
                    )
                    FROM visa_sub_codes s WHERE s.parent_code = v.code
                )
            )
        ) ORDER BY v.sort_order
    )
    FROM visas v;
    """
    try:
        async with db_pool.acquire() as conn:
            json_str = await conn.fetchval(query)
            if not json_str:
                return {"data": [], "status": "empty"}
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"DB 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 쿼리 중 오류가 발생했습니다.")

@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    # [보안 패치 1 검증] 동의하지 않은 요청 서버 단에서 원천 차단
    if not req.consent:
        raise HTTPException(status_code=400, detail="개인정보 처리 동의가 필요합니다.")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="서버 내부 오류: AI API 키 누락")

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
        system_prompt += f"\n\n[관련 법령]:\n{law_context}"
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
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                logger.info(f"AI 추론 성공 (사용 모델: {model_name})")
                append_log(category, success=True)
                return {"answer": answer}
                
        except Exception as e:
            logger.warning(f"모델 [{model_name}] 추론 실패: {str(e)}. 다음 모델로 우회 시도.")
            continue
            
    append_log(category, success=False)
    logger.error("치명적 오류: 가용 가능한 모든 AI 모델 호출에 실패했습니다.")
    raise HTTPException(status_code=503, detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.")

# [보안 패치 2] app.mount("/static", ...) 코드 완전 삭제
# 화이트리스트 방식으로 딱 필요한 파일 두 개만 정밀 서빙하여 디렉토리 노출 원천 차단
@app.get("/")
@app.get("/index.html")
async def serve_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="index.html 파일을 찾을 수 없습니다.")

@app.get("/ai")
@app.get("/ai.html")
async def serve_ai():
    if os.path.exists("ai.html"):
        return FileResponse("ai.html")
    raise HTTPException(status_code=404, detail="ai.html 파일을 찾을 수 없습니다.")
