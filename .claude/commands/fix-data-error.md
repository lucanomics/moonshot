---
description: /api/visas 데이터 오류 진단 및 수정
allowed-tools: Bash, Read, Edit, GitHub
---

# /fix-data-error

/api/visas 엔드포인트에서 데이터 오류가 발생했을 때 원인을 진단하고 수정합니다.

## 실행 절차

### 1단계: 서버 상태 확인
- `moonshot_backend_fastapi.py` 및 `server.log` 확인
- uvicorn 프로세스 실행 여부 점검

### 2단계: DB 연결 확인
- `DATABASE_URL` 환경변수 존재 여부 확인
- asyncpg 풀 연결 테스트

### 3단계: /api/visas 응답 검증
- 엔드포인트 직접 호출 후 응답 구조 확인
- `visa_data.json` 54개 항목과 응답 비교

### 4단계: 오류 원인 분류 및 수정
- DB 연결 실패 → DATABASE_URL 또는 Railway PostgreSQL 플러그인 점검
- 응답 구조 불일치 → `moonshot_backend_fastapi.py`의 조립 로직 수정
- seed 데이터 누락 → `migrations/002_seed.sql` 재실행

### 5단계: 수정 후 검증 및 커밋
- /api/visas 재호출로 54건 전수 일치 확인
- 변경사항 커밋 및 푸시
