"""
docs/sajeung-manual.md, docs/ceryu-manual.md → 청크 분할 → BAAI/bge-m3 임베딩 → Supabase manual_chunks.

실행 전 확인:
    1) migrations/002_rag_pgvector.sql 가 Supabase에 적용되어 있어야 함.
    2) 환경변수: HF_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY.
    3) python3 -m pip install supabase httpx python-dotenv

실행:
    python3 scripts/rag/index_manuals.py
옵션:
    --dry-run        : Supabase 삽입 없이 청크/임베딩 호출만 검증
    --source sajeung : 한쪽 파일만 인덱싱
    --reset          : 인덱싱 전 manual_chunks 테이블의 기존 데이터 삭제
"""

from __future__ import annotations
import argparse
import asyncio
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

load_dotenv(ROOT / ".env")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY", ""
)

EMBED_MODEL = "openai/text-embedding-3-small"
EMBED_DIM = 1536
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

VISA_CODE_RE = re.compile(r"\b([A-H]-\d{1,2}(?:-\d{1,3})?)\b")
SECTION_HEADER_RE = re.compile(r"^##\s+([A-H]-\d{1,2}(?:-\d{1,3})?)(?:\s*[—–-]\s*(.+))?\s*$")
PAGE_HEADER_RE = re.compile(r"^###\s+p\.(\d+)\s*$")

SOURCES = [
    {"id": "sajeung", "path": DOCS / "sajeung-manual.md"},
    {"id": "ceryu", "path": DOCS / "ceryu-manual.md"},
]


def _check_env() -> None:
    missing = [k for k, v in [
        ("HF_TOKEN", HF_TOKEN),
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_SERVICE_KEY (또는 SUPABASE_SERVICE_ROLE_KEY)", SUPABASE_SERVICE_KEY),
    ] if not v]
    if missing:
        print("[ERROR] 다음 환경변수가 설정되지 않았습니다:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print("\n.env 또는 export 로 설정 후 다시 실행하세요.", file=sys.stderr)
        sys.exit(1)


def _load_supabase():
    try:
        from supabase import create_client
    except ImportError:
        print("[ERROR] supabase 패키지가 설치되지 않았습니다. pip install supabase", file=sys.stderr)
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def parse_md(md_path: Path):
    """매뉴얼 MD를 (visa_code, page_num, content) 튜플 리스트로 파싱.

    extract_pdf.py가 생성한 구조에 맞춰: ## CODE → ### p.N → 본문.
    """
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_code: str | None = None
    current_page: int | None = None
    buf: list[str] = []
    blocks: list[tuple[str | None, int | None, str]] = []

    def flush():
        if buf:
            content = "\n".join(buf).strip()
            if content:
                blocks.append((current_code, current_page, content))
            buf.clear()

    for ln in lines:
        m_sec = SECTION_HEADER_RE.match(ln)
        if m_sec:
            flush()
            current_code = m_sec.group(1)
            current_page = None
            continue
        m_page = PAGE_HEADER_RE.match(ln)
        if m_page:
            flush()
            current_page = int(m_page.group(1))
            continue
        if ln.startswith("# "):
            continue
        buf.append(ln)
    flush()
    return blocks


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """단락(빈 줄) 우선, 길이 초과 시 슬라이딩 분할 + overlap 적용."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    cur = ""
    for p in paras:
        if len(cur) + len(p) + 2 > size:
            if cur:
                chunks.append(cur.strip())
            if len(p) > size:
                # 단락이 자체로 너무 길면 강제 슬라이딩
                start = 0
                while start < len(p):
                    end = min(start + size, len(p))
                    chunks.append(p[start:end])
                    if end == len(p):
                        break
                    start = end - overlap
                cur = ""
            else:
                cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur:
        chunks.append(cur.strip())
    return chunks


def detect_visa_code(text: str, fallback: str | None) -> str | None:
    """청크 본문을 우선해서 비자 코드를 추정.

    섹션 헤더 기반 fallback은 신뢰도가 낮아(목차/오탐 빈발) 청크에 강한 신호가
    있을 때만 fallback을 무시. 우선순위:
      1) 청크에 단 하나의 코드만 등장 → 그 코드
      2) 여러 코드 등장 → 가장 빈도 높은 코드 (동점 시 fallback 또는 None)
      3) 청크에 코드 미등장 → fallback (섹션) 사용
    """
    from collections import Counter
    codes = [m.group(1) for m in VISA_CODE_RE.finditer(text)]
    if not codes:
        return fallback
    counts = Counter(codes)
    most_common = counts.most_common()
    if len(most_common) == 1:
        return most_common[0][0]
    top_code, top_n = most_common[0]
    second_n = most_common[1][1]
    if top_n >= second_n * 2:
        return top_code
    if fallback and fallback in counts:
        return fallback
    return top_code


async def embed(client: httpx.AsyncClient, text: str, retries: int = 3) -> list[float]:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            res = await client.post(
                EMBED_URL,
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={"model": EMBED_MODEL, "input": text[:4000]},
                timeout=60.0,
            )
            res.raise_for_status()
            data = res.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            last_err = e
            if attempt + 1 < retries:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"embedding failed after {retries} retries: {last_err}")


async def index_source(supabase, src: dict, dry_run: bool):
    md_path: Path = src["path"]
    if not md_path.exists():
        print(f"[{src['id']}] SKIP: {md_path} not found", flush=True)
        return 0

    blocks = parse_md(md_path)
    if not blocks:
        print(f"[{src['id']}] SKIP: no parseable blocks", flush=True)
        return 0

    print(f"[{src['id']}] {len(blocks)} blocks parsed → chunking ...", flush=True)
    items: list[dict] = []
    for code, page, content in blocks:
        for chunk in chunk_text(content):
            visa_code = detect_visa_code(chunk, code)
            items.append({
                "source": src["id"],
                "page_num": page,
                "visa_code": visa_code,
                "content": chunk,
            })
    print(f"[{src['id']}] {len(items)} chunks → embedding ...", flush=True)

    inserted = 0
    async with httpx.AsyncClient(timeout=60.0) as http:
        for i, item in enumerate(items):
            try:
                emb = await embed(http, item["content"])
            except Exception as e:
                print(f"  [WARN] chunk {i} embed failed: {e}", file=sys.stderr)
                continue
            item["embedding"] = emb

            if not dry_run:
                try:
                    supabase.table("manual_chunks").insert(item).execute()
                    inserted += 1
                except Exception as e:
                    print(f"  [WARN] chunk {i} insert failed: {e}", file=sys.stderr)
            else:
                inserted += 1

            if (i + 1) % 25 == 0:
                print(f"  [{src['id']}] {i+1}/{len(items)}", flush=True)
            # rate-limit guard
            await asyncio.sleep(0.05)

    print(f"[{src['id']}] DONE — inserted={inserted}/{len(items)} (dry_run={dry_run})", flush=True)
    return inserted


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reset", action="store_true", help="기존 manual_chunks 데이터 삭제 후 인덱싱")
    ap.add_argument("--source", choices=["sajeung", "ceryu"], default=None)
    args = ap.parse_args()

    if not args.dry_run:
        _check_env()
        supabase = _load_supabase()
    else:
        supabase = None

    if args.reset and not args.dry_run:
        print("[reset] deleting existing rows in manual_chunks ...", flush=True)
        try:
            supabase.table("manual_chunks").delete().neq("id", -1).execute()
        except Exception as e:
            print(f"[reset] failed: {e}", file=sys.stderr)
            sys.exit(1)

    started = time.time()
    total = 0
    for src in SOURCES:
        if args.source and src["id"] != args.source:
            continue
        total += await index_source(supabase, src, args.dry_run)
    elapsed = time.time() - started
    print(f"\n=== ALL DONE — total inserted={total}, elapsed={elapsed:.1f}s ===", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
