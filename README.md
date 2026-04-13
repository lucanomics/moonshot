# Moonshot

Official-source immigration guidance pipeline for Hi Korea and Korea Immigration Service.

## Files
- moonshot_pipeline_architecture.md: 전체 구조 문서
- moonshot_schema.sql: PostgreSQL 테이블 생성 스키마
- seed_registry_insert.sql: 공식 시드 URL 등록 SQL
- moonshot_crawler.py: 공식 사이트 HTML/PDF 수집기
- moonshot_backend_fastapi.py: FastAPI 백엔드 골격
- moonshot_api_spec.yaml: 검색 API 명세
- moonshot_admin_review_spec.md: 관리자 검수 화면 스펙

## Basic flow
1. Run `moonshot_schema.sql`
2. Run `seed_registry_insert.sql`
3. Test `moonshot_crawler.py`
4. Run `moonshot_backend_fastapi.py`

## Notes
- Official domains only
- No automatic publication without review
- Show official URL and last verified date in public results
