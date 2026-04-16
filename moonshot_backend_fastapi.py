import os
import json
import logging
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MoonshotBackend")

app = FastAPI(title="Moonshot API")

# 보안 통제: 허용된 메서드 및 최소한의 CORS 정책 적용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 실제 도메인으로 엄격히 제한할 것
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 전역 데이터 캐시 (I/O 병목 제거)
cached_visa_data = []

@app.on_event("startup")
async def startup_event():
    global cached_visa_data
    try:
        with open("visa_data.json", "r", encoding="utf-8") as f:
            cached_visa_data = json.load(f)
        logger.info(f"메모리에 {len(cached_visa_data)}개의 비자 데이터를 적재 완료했습니다.")
    except Exception as e:
        logger.error(f"비자 데이터 적재 실패 (경로 및 파일명 확인 필수): {e}")

class AskRequest(BaseModel):
    question: str
    consent: bool
    context: Optional[str] = ""

async def search_law(query: str) -> str:
    """국가법령정보센터 API 연동 뼈대 (RAG)"""
    law_api_key = os.environ.get("LAW_API_KEY")
    if not law_api_key:
        logger.warning("LAW_API_KEY 누락: 법령 실시간 검색이 생략됩니다.")
        return ""
    # 추후 외부 검색 API 연동 로직 구현부
    return ""

@app.get("/api/visas")
async def get_visas():
    if not cached_visa_data:
        logger.warning("캐시된 비자 데이터가 없습니다.")
        return {"data": [], "status": "empty"}
    return cached_visa_data

@app.post("/api/ask")
async def ask_ai(req: AskRequest):
    if not req.consent:
        raise HTTPException(status_code=400, detail="개인정보 처리 동의가 필요합니다.")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY가 환경 변수에 존재하지 않습니다.")
        raise HTTPException(status_code=500, detail="서버 내부 오류: AI API 키 누락")

    law_context = await search_law(req.question)

    # 4대 제약 조건 및 범용 페르소나 명문화
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

    # 다중 LLM 순차 폴백 라우팅
    models_to_try = [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

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
                return {"answer": answer}
                
        except Exception as e:
            logger.warning(f"모델 [{model_name}] 추론 실패: {str(e)}. 다음 모델로 우회 시도.")
            continue
            
    logger.error("치명적 오류: 가용 가능한 모든 AI 모델 호출에 실패했습니다.")
    raise HTTPException(status_code=503, detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.")

# 정적 파일 서빙: 보안을 위해 명시된 파일만 제공
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
