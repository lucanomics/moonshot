# RAG 운영 가이드

법무부 사증·체류민원 매뉴얼을 Supabase pgvector에 인덱싱해 `/api/ask` 답변을 매뉴얼 근거로 강제하는 파이프라인.

```
PDF (docs/*.pdf)
   │
   ▼  pdfplumber + 자간 중복 제거 + 비자코드 섹션 분할
docs/sajeung-manual.md, docs/ceryu-manual.md
   │
   ▼  단락 우선 청크(800자/100자 overlap) + BAAI/bge-m3 임베딩
Supabase manual_chunks (pgvector vector(1024))
   │
   ▼  /api/ask: 사용자 질문 임베딩 → match_manual_chunks RPC
top-K 청크를 system+user prompt 앞에 prepend
```

## 1. 환경변수
`.env` 또는 Railway Variables 에 추가:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...   # service_role key (인덱싱 + RPC)
HF_TOKEN=hf_...               # https://huggingface.co/settings/tokens (read 권한)
```

## 2. 1회: Supabase 스키마 적용
1. Supabase Dashboard → SQL Editor → New query
2. `migrations/002_rag_pgvector.sql` 전체 붙여넣기 → Run
3. 확인 SQL:
   ```sql
   select extname from pg_extension where extname = 'vector';
   select count(*) from manual_chunks;
   ```

## 3. PDF → 마크다운 추출
```bash
pip install pdfplumber
python3 scripts/rag/extract_pdf.py
```
출력:
- `docs/sajeung-manual.md`
- `docs/ceryu-manual.md`

자간 효과로 글자가 중복되는 표지·헤더는 자동 정리. 표는 마크다운 테이블로 변환. 텍스트 추출이 거의 안 되는 페이지는 `[스캔 페이지 - 텍스트 추출 불가]` 마킹.

## 4. 마크다운 → 임베딩 → Supabase 적재
```bash
pip install supabase httpx python-dotenv
# 사전 점검 (네트워크 호출만, DB 미수정)
python3 scripts/rag/index_manuals.py --dry-run

# 본 실행 (기존 데이터 모두 삭제 후 재인덱싱)
python3 scripts/rag/index_manuals.py --reset

# 한쪽만
python3 scripts/rag/index_manuals.py --source sajeung
```
- 임베딩 모델: `BAAI/bge-m3` (1024차원, 한국어 강함)
- 청크 크기 800자 / overlap 100자
- HF API rate-limit 보호용 50ms 슬립

## 5. 백엔드 동작 (자동)
`moonshot_backend_fastapi.py` 의 `/api/ask` 가 매 요청마다:
1. `retrieve_manual_context(question, visa_code)` 호출
2. `visa_code` 가 있으면 그 코드로 필터된 검색 → 결과 비면 전체 검색으로 fallback
3. 검색 결과를 user prompt 최상단에 `[참고 자료 — 법무부 매뉴얼 벡터 검색 결과]` 블록으로 prepend
4. 환경변수 미설정·임베딩 실패·RPC 오류 시 빈 문자열 → 기존 `visa_data` + 공공데이터 RAG 캐시로만 동작

기존 OpenRouter/Groq 폴백 체인, 공공데이터 캐시(`init_public_data_cache`), 국가법령 실시간 조회(`fetch_realtime_law_data`)는 그대로 유지됩니다.

## 6. 매뉴얼 갱신 시
법무부가 매뉴얼을 새로 발행하면:
1. 새 PDF 를 `docs/` 에 교체
2. `python3 scripts/rag/extract_pdf.py` 재실행 (마크다운 갱신)
3. `python3 scripts/rag/index_manuals.py --reset` (테이블 초기화 후 재인덱싱)

## 7. 문제 해결
| 증상 | 원인 | 조치 |
|---|---|---|
| `RAG 임베딩 실패` 로그 | HF_TOKEN 미설정/만료 | 토큰 재발급 후 재시작 |
| `RAG RPC 실패` 로그 | Supabase 키 오타, RLS 정책 | service_role key 확인, 002 SQL 재적용 |
| `/api/ask` 응답에 매뉴얼 발췌 미포함 | 인덱싱 미완료 | `select count(*) from manual_chunks` 확인 |
| 임베딩 차원 오류 | 모델 변경 | `vector(차원)` 과 `match_manual_chunks` 시그니처 동시 수정 |
