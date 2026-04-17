import os
import json
import asyncio
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 환경 변수 적재
load_dotenv()

LAW_API_KEY = os.environ.get("LAW_API_KEY")
BASE_URL = "http://www.law.go.kr/DRF/lawService.do"

# 타겟 법령 지정 (출입국 실무의 근간)
TARGET_LAWS = ["출입국관리법", "출입국관리법 시행령", "출입국관리법 시행규칙"]

async def fetch_law_details(client: httpx.AsyncClient, law_name: str) -> dict:
    """국가법령정보센터 API에서 특정 법령의 조문 단위 원시 데이터를 추출한다."""
    # 1. 법령 ID(MST) 검색
    search_params = {
        "OC": LAW_API_KEY,
        "target": "law",
        "type": "XML",
        "query": law_name
    }
    
    search_resp = await client.get(BASE_URL, params=search_params)
    search_resp.raise_for_status()
    search_soup = BeautifulSoup(search_resp.text, "xml")
    
    law_id_node = search_soup.find("법령일련번호")
    if not law_id_node:
        print(f"[{law_name}] 검색 실패: API 키 또는 법령명을 확인하라.")
        return None
        
    law_id = law_id_node.text
    
    # 2. 법령 본문 조문 단위 정밀 추출
    detail_params = {
        "OC": LAW_API_KEY,
        "target": "law",
        "type": "XML",
        "MST": law_id
    }
    
    detail_resp = await client.get(BASE_URL, params=detail_params)
    detail_resp.raise_for_status()
    detail_soup = BeautifulSoup(detail_resp.text, "xml")
    
    articles = []
    # XML 태그 내 '조문단위'를 순회하며 제목과 내용을 직렬화
    for article in detail_soup.find_all("조문단위"):
        title = article.find("조문제목")
        content = article.find("조문내용")
        if title and content:
            articles.append({
                "article_title": title.text.strip(),
                "content": content.text.strip()
            })
            
    return {
        "law_name": law_name,
        "law_id": law_id,
        "articles": articles
    }

async def main():
    if not LAW_API_KEY:
        print("치명적 오류: .env 파일에 LAW_API_KEY가 누락되었다. 즉시 주입하라.")
        return

    print("Moonshot 법령 크롤러 가동 시작...")
    results = []
    
    # 연결 유지 및 병목 방지를 위한 비동기 클라이언트 컨텍스트
    async with httpx.AsyncClient(timeout=30.0) as client:
        for law in TARGET_LAWS:
            print(f"타겟 타격 중: [{law}]")
            data = await fetch_law_details(client, law)
            if data:
                results.append(data)
                print(f"[{law}] 추출 성공: {len(data['articles'])}개 조문 획득.")
                
    # 2단계(ETL) 처리를 위한 원시 데이터 JSON 직렬화 저장
    output_file = "raw_law_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"크롤링 작전 종료: 총 {len(results)}개 법령 데이터가 '{output_file}'에 적재 완료되었다.")

if __name__ == "__main__":
    asyncio.run(main())
