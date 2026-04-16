import json
import os
import psycopg2
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- DB 연결 -----
def get_db_connection():
    return psycopg2.connect(dbname="moonshot")

# ----- 서버 시작 시 JSON → DB 자동 주입 -----
@app.on_event("startup")
def startup_event():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM visa_data;")
        count = cur.fetchone()[0]

        if count == 0:
            print("[Moonshot DB] 빈 데이터베이스 감지. JSON 데이터를 주입합니다...")
            with open("visa_data (1).json", "r", encoding="utf-8") as f:
                visa_list = json.load(f)

            for v in visa_list:
                cur.execute("""
                    INSERT INTO visa_data (code, name, cat, period, data_badge, data_date, new_req, ext_req, faq, aliases, sub_codes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    v.get("code"), v.get("name"), v.get("cat"), v.get("period"),
                    v.get("dataBadge"), v.get("dataDate"), v.get("newReq"),
                    v.get("extReq"), v.get("faq"),
                    json.dumps(v.get("aliases", []), ensure_ascii=False) if v.get("aliases") else '[]',
                    json.dumps(v.get("subCodes", []), ensure_ascii=False) if v.get("subCodes") else '[]'
                ))
            conn.commit()
            print(f"[Moonshot DB] 성공적으로 {len(visa_list)}개의 데이터를 주입했습니다!")
        else:
            print(f"[Moonshot DB] 이미 {count}개의 데이터가 존재합니다. 주입을 건너뜁니다.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Moonshot DB] 시작 오류: {e}")

# ----- 기존 엔드포인트 -----
@app.get("/api/visas")
def get_visas():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, name, cat, period, data_badge, data_date, new_req, ext_req, faq, aliases, sub_codes FROM visa_data;")
        rows = cur.fetchall()

        result = []
        for r in rows:
            result.append({
                "code": r[0], "name": r[1], "cat": r[2], "period": r[3],
                "dataBadge": r[4], "dataDate": r[5], "newReq": r[6],
                "extReq": r[7], "faq": r[8],
                "aliases": json.loads(r[9]) if r[9] else [],
                "subCodes": json.loads(r[10]) if r[10] else []
            })

        cur.close()
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}


# =========================================================
# RAG 기반 AI 질의 엔드포인트 (/api/ask)
# =========================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

# visa_data.json을 메모리에 캐싱 (서버 재시작 시 1회 로드)
_visa_cache: list = []

def load_visa_cache():
    global _visa_cache
    if _visa_cache:
        return _visa_cache
    try:
        with open("visa_data.json", "r", encoding="utf-8") as f:
            _visa_cache = json.load(f)
    except Exception as e:
        print(f"[Moonshot RAG] visa_data.json 로드 실패: {e}")
        _visa_cache = []
    return _visa_cache


def rag_search(query: str, top_k: int = 4) -> list:
    """
    질문에서 키워드를 추출해 visa_data에서 관련 항목만 필터링.
    code / name / aliases / subCodes.name 에서 매칭.
    """
    data = load_visa_cache()
    q_lower = query.lower()

    # 단어 단위 토큰 (2글자 이상만)
    tokens = [t for t in q_lower.replace(",", " ").split() if len(t) >= 2]

    scored = []
    for item in data:
        # 검색 대상 텍스트 구성
        searchable = " ".join(filter(None, [
            item.get("code", ""),
            item.get("name", ""),
            item.get("newReq", ""),
            item.get("faq", ""),
            " ".join(item.get("aliases", [])),
            " ".join(sc.get("name", "") for sc in item.get("subCodes", [])),
        ])).lower()

        score = sum(1 for t in tokens if t in searchable)
        if score > 0:
            scored.append((score, item))

    # 점수 내림차순 정렬, 상위 top_k 반환
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def slim_item(item: dict) -> dict:
    """토큰 절약을 위해 각 항목에서 꼭 필요한 필드만 유지"""
    sub = []
    for sc in item.get("subCodes", [])[:5]:  # 서브코드 최대 5개
        sub.append({
            "code": sc.get("code"),
            "name": sc.get("name"),
            "addReq": sc.get("addReq"),
            "note": sc.get("note"),
        })
    return {
        "code":    item.get("code"),
        "name":    item.get("name"),
        "period":  item.get("period"),
        "newReq":  item.get("newReq"),
        "extReq":  item.get("extReq"),
        "faq":     item.get("faq"),
        "aliases": item.get("aliases", []),
        "subCodes": sub,
    }


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
async def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        return {"error": "질문이 비어 있습니다."}
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY 환경변수가 설정되지 않았습니다."}

    # 1) RAG: 관련 데이터 추출
    hits = rag_search(question, top_k=4)
    context_json = json.dumps([slim_item(h) for h in hits], ensure_ascii=False, separators=(",", ":"))

    # 2) 시스템 프롬프트 (데이터 없을 때 폴백 안내 포함)
    if hits:
        system_prompt = (
            "You are Moonshot AI, a Korean immigration & visa assistant for Jeju Immigration & Customs Service staff. "
            "Answer the question accurately and concisely in the same language as the question (Korean or English). "
            "Use ONLY the provided context data. If the answer cannot be determined from the context, say so clearly.\n\n"
            f"[CONTEXT]\n{context_json}"
        )
    else:
        system_prompt = (
            "You are Moonshot AI, a Korean immigration & visa assistant. "
            "No relevant data was found in the database for this question. "
            "Politely let the user know and suggest they contact 1345 (Korea Immigration Contact Center)."
        )

    # 3) Groq API 호출
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Groq API 오류: {e.response.status_code} — {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}
