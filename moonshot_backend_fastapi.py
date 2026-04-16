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
async def ask_ai(req: AskRequest):
    if not req.consent:
        raise HTTPException(status_code=400, detail="개인정보 처리 동의가 필요합니다.")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set.")
        raise HTTPException(status_code=500, detail="서버에 AI API 키가 설정되지 않았습니다.")

    # [핵심] RAG를 위한 법령 실시간 검색
    law_context = await search_law(req.question)

    # [핵심] 4대 제약 조건이 명문화된 강력한 시스템 프롬프트
    system_prompt = (
        "당신은 대한민국 제주출입국·외국인청 소속의 최고위급 민원 안내 전문 AI 'Moonshot'이다.\n"
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

    # [핵심] 다중 LLM 폴백 라우팅 아키텍처 (우선순위 배열)
    models_to_try = [
        "llama-3.3-70b-versatile", # 1순위: 메인 추론 엔진
        "mixtral-8x7b-32768",      # 2순위: 속도 및 검열 저항 백업
        "gemma2-9b-it"             # 3순위: 서버 과부하 대비 경량 생존 모델
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 순차적 폴백(Fallback) 실행 루프
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question},
            ],
            "max_tokens": 1024,
            "temperature": 0.1,  # 환각 억제를 위한 극저온 설정
            "top_p": 0.9,
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                logger.info(f"AI 응답 성공 (사용 모델: {model_name})")
                return {"answer": answer}
                
        except Exception as e:
            logger.warning(f"모델 [{model_name}] 호출 실패: {str(e)}. 다음 모델로 우회합니다.")
            continue # 실패 시 다음 모델로 이동
            
    # 배열 내의 모든 모델이 실패했을 경우
    logger.error("모든 AI 모델 라우팅 실패 (API 장애)")
    raise HTTPException(status_code=503, detail="현재 모든 AI 서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.")

    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
    if req.consent:
        append_log(category, success=True)
    return {"answer": answer}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 서버가 현재 폴더의 파일들을 서비스하도록 설정
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/ai")
@app.get("/ai.html")
async def read_ai():
    return FileResponse("ai.html")

@app.get("/")
@app.get("/index.html")
async def read_index():
    return FileResponse("index.html")
