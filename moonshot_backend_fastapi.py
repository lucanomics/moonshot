import json
import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 (프론트엔드 HTML에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    # Mac 환경 로컬 DB 연결
    return psycopg2.connect(dbname="moonshot")

@app.on_event("startup")
def startup_event():
    # 서버 켜질 때 DB가 비어있으면 JSON 파일을 읽어서 자동 주입 (Seeding)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM visa_data;")
        count = cur.fetchone()[0]
        
        if count == 0:
            print("[Moonshot DB] 빈 데이터베이스 감지. JSON 데이터를 주입합니다...")
            # GitHub 저장소에 있는 JSON 파일명과 일치해야 함
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
        print(f"[Moonshot DB] 시작 오류 (데이터 주입 실패): {e}")

@app.get("/api/visas")
def get_visas():
    # 프론트엔드로 데이터를 쏴주는 핵심 API 엔드포인트
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT code, name, cat, period, data_badge, data_date, new_req, ext_req, faq, aliases, sub_codes FROM visa_data;")
        rows = cur.fetchall()
        
        result = []
        for r in rows:
            result.append({
                "code": r[0],
                "name": r[1],
                "cat": r[2],
                "period": r[3],
                "dataBadge": r[4],
                "dataDate": r[5],
                "newReq": r[6],
                "extReq": r[7],
                "faq": r[8],
                "aliases": json.loads(r[9]) if r[9] else [],
                "subCodes": json.loads(r[10]) if r[10] else []
            })
            
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}
