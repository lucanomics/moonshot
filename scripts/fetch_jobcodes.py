#!/usr/bin/env python3
"""
통계청 산업직업분류 데이터 수집 스크립트 (2025.09.01 기준)
─────────────────────────────────────────────────────────────
Moonshot 프로젝트용: 공공데이터포털 오픈API에서 KSCO+KSIC 전체 데이터를
수집하여 jobcode_master.json으로 저장합니다.

사용법:
    1. 공공데이터포털에서 발급받은 "일반 인증키(Decoding)"를 환경변수로 설정
       $ export JOBCODE_API_KEY="본인의_Decoding_키_붙여넣기"
    
    2. 스크립트 실행
       $ python3 scripts/fetch_jobcodes.py
    
    3. 결과 파일 확인: data/jobcode_master.json

주의:
    - 반드시 "Decoding" 키를 사용하세요. "Encoding" 키는 URL 이중 인코딩으로 401 오류 발생.
    - 일일 호출 한도 주의 (일반적으로 1,000회, 이 스크립트는 ~10회 사용).
    - 발급 직후 1시간 정도 활성화 지연이 있을 수 있습니다.

API 정보:
    출처: 통계청_산업직업분류_20250901
    URL: https://api.odcloud.kr/api/15117819/v1/uddi:3e1a696a-a0a2-4cbb-b5ca-d67a4f9ab09d
    활용신청: https://www.data.go.kr/data/15117819/openapi.do
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from collections import Counter

# ========================================================================
# 설정
# ========================================================================
API_BASE = "https://api.odcloud.kr/api/15117819/v1/uddi:3e1a696a-a0a2-4cbb-b5ca-d67a4f9ab09d"
PER_PAGE = 1000            # 한 번에 가져올 행 수 (최대 1000 권장)
MAX_PAGES = 20             # 무한루프 방지용 상한 (2400개면 3페이지면 충분)
REQUEST_DELAY = 0.3        # 페이지 간 딜레이 (초) - 서버 부담 최소화
OUTPUT_PATH = Path("data/jobcode_master.json")
USER_AGENT = "Moonshot-JobcodeFetcher/1.0 (Jeju Immigration Office public service tool)"


# ========================================================================
# 유틸리티
# ========================================================================
def log(msg, level="INFO"):
    """타임스탬프 + 레벨 포함 로그 출력."""
    stamp = time.strftime("%H:%M:%S")
    icon = {"INFO": "i", "OK": "v", "WARN": "!", "ERR": "x", "STEP": ">"}.get(level, "-")
    print(f"[{stamp}] {icon} {msg}", flush=True)


def die(msg, code=1):
    """치명적 오류 출력 후 종료."""
    log(msg, "ERR")
    log("스크립트를 종료합니다.", "ERR")
    sys.exit(code)


def fetch_page(api_key, page):
    """단일 페이지 API 호출. 응답 JSON 딕셔너리 반환."""
    params = {
        "page": page,
        "perPage": PER_PAGE,
        "serviceKey": api_key,
        "returnType": "JSON",
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            die(
                "인증 실패 (401). 원인 후보:\n"
                "  1. API 키가 틀렸거나 오탈자 있음\n"
                "  2. Encoding 키를 사용했음 (반드시 Decoding 키 사용)\n"
                "  3. 활용신청 승인 후 1시간 미경과 (기다렸다 재시도)\n"
                "  4. 일일 트래픽 한도 초과"
            )
        elif e.code == 429:
            die("트래픽 제한 초과 (429). 24시간 뒤 재시도하세요.")
        else:
            die(f"HTTP 오류 {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        die(f"네트워크 오류: {e.reason}")
    except json.JSONDecodeError as e:
        die(f"응답을 JSON으로 파싱 실패: {e}")


# ========================================================================
# 메인 로직
# ========================================================================
def main():
    log("통계청 산업직업분류 데이터 수집 시작", "STEP")
    log("대상 API: 통계청_산업직업분류_20250901")

    # 1. API 키 확인
    api_key = os.environ.get("JOBCODE_API_KEY", "").strip()
    if not api_key:
        die(
            "환경변수 JOBCODE_API_KEY가 설정되어 있지 않습니다.\n"
            "  실행 전에 다음 명령을 먼저 입력하세요:\n"
            '  $ export JOBCODE_API_KEY="본인의_Decoding_키_붙여넣기"'
        )
    log(f"API 키 로드 완료 (길이 {len(api_key)}자)", "OK")

    # 2. 페이지네이션 반복 호출
    all_rows = []
    total_count = None

    for page in range(1, MAX_PAGES + 1):
        log(f"페이지 {page} 요청 중...", "STEP")
        data = fetch_page(api_key, page)

        # 첫 응답에서 전체 개수 기록
        if total_count is None:
            total_count = data.get("totalCount", 0)
            log(f"전체 데이터 개수: {total_count:,}건", "INFO")
            if total_count == 0:
                die("전체 개수가 0입니다. API 상태 또는 키 권한을 확인하세요.")

        rows = data.get("data", [])
        if not rows:
            log(f"페이지 {page}에 데이터 없음 — 수집 종료", "INFO")
            break

        all_rows.extend(rows)
        log(f"  → {len(rows)}건 수신 (누적 {len(all_rows):,}/{total_count:,})", "OK")

        if len(all_rows) >= total_count:
            log("전체 데이터 수집 완료", "OK")
            break

        time.sleep(REQUEST_DELAY)
    else:
        log(f"최대 페이지 수({MAX_PAGES}) 도달. 루프 종료.", "WARN")

    # 3. 정합성 검증
    log("수집 데이터 검증 중...", "STEP")
    if len(all_rows) == 0:
        die("수집된 데이터가 0건입니다.")
    if len(all_rows) < total_count:
        log(f"경고: 기대치({total_count})보다 적게 수집됨({len(all_rows)})", "WARN")

    # 샘플 구조 확인
    sample = all_rows[0]
    required_keys = {"분류", "코드값", "상세설명"}
    missing = required_keys - set(sample.keys())
    if missing:
        log(f"경고: 기대하는 키가 누락됨: {missing}. 실제 키: {list(sample.keys())}", "WARN")

    # 4. 분류별 통계
    log("분류별 분포:", "INFO")
    category_counts = Counter(row.get("분류", "UNKNOWN") for row in all_rows)
    for cat, cnt in category_counts.most_common():
        log(f"  - {cat}: {cnt:,}건", "INFO")

    # 5. 파일 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "source": "공공데이터포털 - 통계청_산업직업분류_20250901",
        "source_url": "https://www.data.go.kr/data/15117819/openapi.do",
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(all_rows),
        "categories": dict(category_counts),
        "data": all_rows,
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    log(f"파일 저장 완료: {OUTPUT_PATH} ({size_kb:,.1f} KB)", "OK")
    log("-" * 60, "INFO")
    log("수집 완료! 이 파일을 GitHub에 커밋하면 됩니다.", "OK")
    log(f"   git add {OUTPUT_PATH}", "INFO")
    log('   git commit -m "Add jobcode master data (KSCO+KSIC 20250901)"', "INFO")
    log("   git push", "INFO")


if __name__ == "__main__":
    main()
