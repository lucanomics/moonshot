-- =====================================================================
-- 002_rag_pgvector.sql
-- 법무부 사증·체류민원 매뉴얼 RAG 인덱싱용 pgvector 테이블 + 검색 함수.
--
-- 실행 방법:
--   Supabase Dashboard → SQL Editor → 새 쿼리 → 본 파일 전체 붙여넣기 → Run
--
-- 참고:
--   임베딩 차원(1024)은 BAAI/bge-m3 모델 출력 기준.
--   임베딩 모델을 바꿀 경우 vector(차원) 값과 인덱스를 함께 갱신.
-- =====================================================================

-- 1) pgvector 확장
create extension if not exists vector;

-- 2) 청크 테이블
create table if not exists manual_chunks (
  id          bigserial primary key,
  source      text   not null check (source in ('sajeung', 'ceryu')),
  page_num    int,
  visa_code   text,
  content     text   not null,
  embedding   vector(1024),
  created_at  timestamptz not null default now()
);

-- 3) 보조 인덱스
create index if not exists manual_chunks_visa_code_idx on manual_chunks (visa_code);
create index if not exists manual_chunks_source_idx     on manual_chunks (source);

-- 4) 벡터 유사도 인덱스 (코사인 거리)
--    rows 가 적을 땐 IVFFLAT 보다 HNSW 가 정확도/속도 면에서 유리
create index if not exists manual_chunks_embedding_hnsw_idx
  on manual_chunks
  using hnsw (embedding vector_cosine_ops);

-- 5) 검색 RPC
--    filter_visa_code 가 주어지면 prefix 매칭 (예: 'E-7' → E-7, E-7-1, E-7-4 모두 포함).
--    하위 코드까지 묶어서 검색해야 RAG 누락이 줄어듦.
create or replace function match_manual_chunks (
  query_embedding   vector(1024),
  match_count       int     default 5,
  filter_visa_code  text    default null
)
returns table (
  id          bigint,
  source      text,
  page_num    int,
  visa_code   text,
  content     text,
  similarity  float
)
language sql stable
as $$
  select
    id,
    source,
    page_num,
    visa_code,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from manual_chunks
  where embedding is not null
    and (
      filter_visa_code is null
      or visa_code = filter_visa_code
      or visa_code like (filter_visa_code || '-%')
    )
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- 6) RLS 정책 (서비스 키만 수정 가능, 익명/인증 사용자는 read-only)
alter table manual_chunks enable row level security;

drop policy if exists manual_chunks_read_all on manual_chunks;
create policy manual_chunks_read_all
  on manual_chunks
  for select
  using (true);

-- 인덱싱은 service_role 키로만 진행하므로 별도 INSERT/UPDATE 정책은 두지 않음.
