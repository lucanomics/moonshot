# Moonshot

## Files
- moonshot_pipeline_architecture.md: 전체 구조
- moonshot_schema.sql: PostgreSQL 스키마
- seed_registry_insert.sql: 공식 시드 URL 등록 SQL
- moonshot_crawler.py: 공식 사이트 수집기
- moonshot_backend_fastapi.py: FastAPI 백엔드

## Order
1. moonshot_schema.sql 실행
2. seed_registry_insert.sql 실행
3. moonshot_crawler.py 테스트
4. moonshot_backend_fastapi.py 실행
