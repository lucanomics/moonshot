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

# CORS 정책
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 실제 도메인으로 제한
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 전역 데이터 캐시
cached_visa_data = []

@app.on_event("startup")
async def startup_event():
    global cached_visa_data
    try:
        with open("visa_data.json", "r", encoding="utf-8") as f:
            cached_visa_data = json.load(f)
        logger.info(f"메모리에 {len(cached_visa_data)}개의 비자 데이터를 적재 완료했습니다.")
    except Exception as e:
        logger.error(f"비자 데이터 적재 실패: {e}")


class AskRequest(BaseModel):
    question: str
    consent: bool
    context: Optional[str] = ""


# ─────────────────────────────────────────────
# 법제처 국가법령정보 공유서비스 OpenAPI 연동
# API 문서: https://open.law.go.kr/LSO/openApi/openApiList.do
# ─────────────────────────────────────────────
LAW_API_BASE = "https://www.law.go.kr/DRF"

async def search_law(query: str) -> str:
    """법제처 OpenAPI로 관련 법령 조문을 검색하여 RAG 컨텍스트 문자열 반환"""
    law_api_key = os.environ.get("LAW_API_KEY")
    if not law_api_key:
        logger.warning("LAW_API_KEY 누락: 법령 실시간 검색이 생략됩니다.")
        return ""

    try:
        # 1단계: 법령 목록 검색 (lawSearch)
        search_url = f"{LAW_API_BASE}/lawSearch.do"
        search_params = {
            "OC": law_api_key,
            "target": "law",
            "type": "JSON",
            "query": query,
            "display": 3,  # 상위 3개 법령만 가져옴
            "sort": "lasc",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(search_url, params=search_params)
            resp.raise_for_status()
            search_data = resp.json()

        laws = search_data.get("LawSearch", {}).get("law", [])
        if not laws:
            logger.info(f"법제처 검색 결과 없음: '{query}'")
            return ""

        # 2단계: 각 법령의 조문 내용 조회 (lawService)
        context_parts = []
        async with httpx.AsyncClient(timeout=8.0) as client:
            for law in laws[:3]:
                law_id = law.get("법령ID") or law.get("MST")
                law_name = law.get("법령명한글", "")
                if not law_id:
                    continue

                article_url = f"{LAW_API_BASE}/lawService.do"
                article_params = {
                    "OC": law_api_key,
                    "target": "law",
                    "type": "JSON",
                    "ID": law_id,
                }
                try:
                    art_resp = await client.get(article_url, params=article_params)
                    art_resp.raise_for_status()
                    art_data = art_resp.json()

                    # 조문 본문 추출
                    articles = (
                        art_data.get("법령", {})
                        .get("조문", {}).get("조문단위", [])
                    )
                    if isinstance(articles, dict):
                        articles = [articles]

                    # 쿼리 키워드 포함 조문만 필터링 (최대 5개)
                    relevant = []
                    for art in articles:
                        content = art.get("조문내용", "") or ""
                        title = art.get("조문제목", "") or ""
                        if any(kw in content or kw in title for kw in query.split()):
                            relevant.append(f"[{law_name}] {title}\n{content}")
                        if len(relevant) >= 5:
                            break

                    if relevant:
                        context_parts.extend(relevant)

                except Exception as e:
                    logger.warning(f"조문 조회 실패 ({law_name}): {e}")
                    continue

        if not context_parts:
            return ""

        result = "\n\n".join(context_parts)
        logger.info(f"법제처 컨텍스트 구성 완료: {len(context_parts)}개 조문 ({len(result)}자)")
        return result

    except Exception as e:
        logger.error(f"법제처 API 호출 오류: {e}")
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

    # 법제처 실시간 법령 컨텍스트 조회
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

    models_to_try = [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
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
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                logger.info(f"AI 추론 성공 (모델: {model_name})")
                return {"answer": answer}
        except Exception as e:
            logger.warning(f"모델 [{model_name}] 실패: {str(e)}. 다음 모델 시도.")
            continue

    logger.error("모든 AI 모델 호출 실패")
    raise HTTPException(
        status_code=503,
        detail="현재 AI 서버 트래픽 폭주로 응답할 수 없습니다. 잠시 후 시도하십시오.",
    )


# 정적 파일 서빙
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
