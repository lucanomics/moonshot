"""
법무부 사증·체류민원 매뉴얼 PDF → 구조화된 마크다운 변환기.

- pdfplumber로 페이지별 텍스트/표 추출
- 자간 효과로 인한 글자 중복 제거 (예: "사사증증" → "사증")
- 비자 코드 패턴(예: 특정활동(E-7))을 헤더로 감지해 ## 섹션 분할
- 표는 마크다운 테이블로 변환
- 텍스트가 거의 없는 페이지는 [스캔 페이지 - 텍스트 추출 불가] 마킹

실행:
    python3 scripts/rag/extract_pdf.py
출력:
    docs/sajeung-manual.md
    docs/ceryu-manual.md
"""

from __future__ import annotations
import os
import re
import sys
import json
import time
import logging
import unicodedata
import multiprocessing as mp
from pathlib import Path

# pypdf 우선, 표 추출은 pdfplumber lazy-load
import pypdf

logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

def _find_pdf(keyword: str) -> Path | None:
    """파일명 NFD/NFC 차이 우회 — 한글 정규화 후 부분 일치 키워드로 탐색."""
    target = unicodedata.normalize("NFC", keyword)
    for p in DOCS.glob("*.pdf"):
        if target in unicodedata.normalize("NFC", p.name):
            return p
    return None


_SAJEUNG = _find_pdf("사증")
_CERYU = _find_pdf("체류")

PDFS = [
    {
        "src": _SAJEUNG,
        "dst": DOCS / "sajeung-manual.md",
        "title": "법무부 사증발급 안내 매뉴얼 (2026.03)",
        "source_id": "sajeung",
    },
    {
        "src": _CERYU,
        "dst": DOCS / "ceryu-manual.md",
        "title": "외국인 체류 안내 매뉴얼 (2026.03)",
        "source_id": "ceryu",
    },
]

# 비자 코드 패턴: A-1, B-2, C-3, D-10, E-7, E-7-4, F-2-99, G-1, H-2 등
VISA_CODE_RE = re.compile(r"\b([A-H]-\d{1,2}(?:-\d{1,3})?)\b")

# 섹션 헤더 추정 패턴 — TOC와 본문 첫 줄에 자주 등장
# 예: "1. 외교(A-1)", "25. 특정활동(E-7)", "특정활동 ( E - 7 )"
SECTION_HEADER_RE = re.compile(
    r"^(?:\d{1,3}\.\s*)?([가-힣A-Za-z·\s]{1,30}?)\s*\(\s*([A-H])\s*[-‐]\s*(\d{1,2})(?:\s*[-‐]\s*(\d{1,3}))?\s*\)\s*$"
)

# 자간 중복 제거: "사사증증" → "사증", "매매 뉴뉴 얼얼" → "매 뉴 얼"
# 단, 정상적인 단어("같았었"같은 패턴은 보존)는 건드리지 않도록 한글만 처리
HANGUL_DOUBLED_RE = re.compile(r"([가-힣])\1")


def dedup_doubled_hangul(line: str) -> str:
    """표지/제목에서 자간 효과로 인한 한글 중복을 제거.

    페이지 전체에서 중복 비율이 30%↑인 경우만 적용 (오탐 방지).
    """
    hangul_chars = re.findall(r"[가-힣]", line)
    if len(hangul_chars) < 4:
        return line
    doubled = sum(1 for m in HANGUL_DOUBLED_RE.finditer(line))
    if doubled * 2 / max(1, len(hangul_chars)) >= 0.3:
        return HANGUL_DOUBLED_RE.sub(r"\1", line)
    return line


def clean_page_text(raw: str) -> str:
    if not raw:
        return ""
    out_lines = []
    for ln in raw.splitlines():
        ln = ln.rstrip()
        if not ln.strip():
            out_lines.append("")
            continue
        out_lines.append(dedup_doubled_hangul(ln))
    # 연속 공백 라인 압축
    cleaned: list[str] = []
    prev_blank = False
    for ln in out_lines:
        is_blank = not ln.strip()
        if is_blank and prev_blank:
            continue
        cleaned.append(ln)
        prev_blank = is_blank
    return "\n".join(cleaned).strip()


def table_to_markdown(table: list[list[str | None]]) -> str:
    """pdfplumber 테이블 → 마크다운 표. 빈 헤더는 자동 보정."""
    if not table or not any(any(c for c in row) for row in table):
        return ""
    rows = [[(c or "").strip().replace("\n", " ") for c in row] for row in table]
    # 너비 정규화
    width = max(len(r) for r in rows)
    for r in rows:
        while len(r) < width:
            r.append("")
    header = rows[0]
    if not any(header):
        header = [f"col{i+1}" for i in range(width)]
        body = rows
    else:
        header = [h or f"col{i+1}" for i, h in enumerate(header)]
        body = rows[1:]
    out = ["| " + " | ".join(header) + " |"]
    out.append("| " + " | ".join(["---"] * width) + " |")
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def detect_section_change(line: str) -> tuple[str, str] | None:
    """라인이 새 섹션 헤더인지 감지. 반환: (visa_code, 섹션 제목) 또는 None."""
    s = line.strip()
    m = SECTION_HEADER_RE.match(s)
    if not m:
        return None
    name, a, b, c = m.group(1), m.group(2), m.group(3), m.group(4)
    code = f"{a}-{b}" + (f"-{c}" if c else "")
    return code, name.strip()


def _extract_text_pypdf(src_str: str, page_idx: int) -> tuple[int, str]:
    """워커 프로세스에서 호출: pypdf로 단일 페이지 텍스트 추출."""
    import pypdf as _pypdf, logging as _lg
    _lg.getLogger("pypdf").setLevel(_lg.ERROR)
    reader = _pypdf.PdfReader(src_str)
    return page_idx, reader.pages[page_idx].extract_text() or ""


def _extract_tables_pdfplumber(src_str: str, page_idx: int) -> tuple[int, list]:
    """표 추출은 pdfplumber로 (느리지만 정확). 별도 워커."""
    try:
        import pdfplumber
        with pdfplumber.open(src_str) as pdf:
            tables = pdf.pages[page_idx].extract_tables() or []
            return page_idx, tables
    except Exception:
        return page_idx, []


def extract_pdf(src: Path, source_id: str, with_tables: bool = False, workers: int = 2) -> dict:
    """pypdf 멀티프로세스 텍스트 추출 + 선택적 pdfplumber 표 추출.

    with_tables 기본값을 False 로 변경 — 텍스트 RAG 가 우선.
    """
    src_str = str(src)
    with pypdf.PdfReader(src_str) as reader:
        total = len(reader.pages)

    print(f"[{source_id}] phase 1/2: text extraction (pypdf, {workers} workers)", flush=True)
    pages: list[dict] = [{} for _ in range(total)]
    started = time.time()
    last_log = started

    with mp.Pool(workers) as pool:
        for done, (idx, text) in enumerate(
            pool.imap_unordered(_text_worker, [(src_str, i) for i in range(total)], chunksize=8),
            start=1,
        ):
            cleaned = clean_page_text(text)
            pages[idx] = {
                "num": idx + 1,
                "text": cleaned,
                "tables": [],
                "scanned": len(cleaned) < 30,
            }
            now = time.time()
            if done % 50 == 0 or done == total or (now - last_log) > 20:
                print(f"  [{source_id}] text {done}/{total} ({now-started:.1f}s elapsed)", flush=True)
                last_log = now

    if with_tables:
        print(f"[{source_id}] phase 2/2: table extraction (pdfplumber, {workers} workers)", flush=True)
        started2 = time.time()
        last_log = started2
        with mp.Pool(workers) as pool:
            for done, (idx, tables) in enumerate(
                pool.imap_unordered(_tables_worker, [(src_str, i) for i in range(total)], chunksize=4),
                start=1,
            ):
                tables_md: list[str] = []
                for t in tables:
                    md = table_to_markdown(t)
                    if md:
                        tables_md.append(md)
                pages[idx]["tables"] = tables_md
                if tables_md:
                    pages[idx]["scanned"] = False
                now = time.time()
                if done % 50 == 0 or done == total or (now - last_log) > 20:
                    print(f"  [{source_id}] tables {done}/{total} ({now-started2:.1f}s elapsed)", flush=True)
                    last_log = now

    return {"pages": pages, "total": total}


def _text_worker(args):
    return _extract_text_pypdf(*args)


def _tables_worker(args):
    return _extract_tables_pdfplumber(*args)


def split_into_sections(pages: list[dict]) -> list[dict]:
    """페이지 시퀀스를 비자 코드 섹션으로 분할."""
    sections: list[dict] = []
    current = {"code": "_PREAMBLE", "name": "서두/목차", "pages": [], "page_start": 1}

    for p in pages:
        # 본문 첫 비-공백 라인부터 위로 5줄 스캔하여 섹션 헤더 탐지
        head_lines = [ln for ln in p["text"].splitlines() if ln.strip()][:5]
        new_section = None
        for ln in head_lines:
            res = detect_section_change(ln)
            if res:
                new_section = res
                break
        if new_section:
            code, name = new_section
            if current["pages"]:
                sections.append(current)
            current = {"code": code, "name": name, "pages": [p], "page_start": p["num"]}
        else:
            current["pages"].append(p)
    if current["pages"]:
        sections.append(current)
    return sections


def render_md(meta: dict, pages: list[dict], sections: list[dict]) -> str:
    """최종 마크다운. 섹션 단위로 ## 헤더 + 페이지 단위 본문/표."""
    out: list[str] = []
    out.append(f"# {meta['title']}")
    out.append("")
    out.append(f"- 출처 PDF: `{meta['src'].name}`")
    out.append(f"- 총 페이지: {len(pages)}")
    out.append(f"- 추출 도구: pypdf (텍스트) + pdfplumber (선택적 표)")
    out.append("- 자동 추출 결과이며 표지/목차의 자간 효과 글자 중복은 자동 제거되었습니다.")
    out.append("")
    out.append("---")
    out.append("")

    for sec in sections:
        title = f"## {sec['code']}" + (f" — {sec['name']}" if sec["name"] and sec["code"] != "_PREAMBLE" else "")
        if sec["code"] == "_PREAMBLE":
            title = "## 서두 및 목차"
        out.append(title)
        out.append("")
        out.append(f"_페이지 범위: p.{sec['page_start']} – p.{sec['pages'][-1]['num']}_")
        out.append("")
        for p in sec["pages"]:
            out.append(f"### p.{p['num']}")
            out.append("")
            if p["scanned"]:
                out.append("[스캔 페이지 - 텍스트 추출 불가]")
                out.append("")
                continue
            if p["text"]:
                out.append(p["text"])
                out.append("")
            for tmd in p["tables"]:
                out.append(tmd)
                out.append("")
        out.append("")
    return "\n".join(out)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-tables", action="store_true", help="표 추출 포함 (pdfplumber, 4-5배 느림)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)), help="병렬 워커 수")
    ap.add_argument("--source", choices=["sajeung", "ceryu"], default=None)
    args = ap.parse_args()

    if not DOCS.exists():
        print(f"docs/ not found: {DOCS}", file=sys.stderr)
        sys.exit(1)
    for cfg in PDFS:
        if args.source and cfg["source_id"] != args.source:
            continue
        src: Path | None = cfg["src"]
        dst: Path = cfg["dst"]
        if src is None or not src.exists():
            print(f"SKIP: {cfg['source_id']} PDF not found in docs/", file=sys.stderr)
            continue
        print(f"[{cfg['source_id']}] extracting {src.name} | workers={args.workers} | with_tables={args.with_tables}", flush=True)
        data = extract_pdf(src, cfg["source_id"], with_tables=args.with_tables, workers=args.workers)
        print(f"[{cfg['source_id']}] splitting into sections ...", flush=True)
        sections = split_into_sections(data["pages"])
        meta = {"title": cfg["title"], "src": src}
        md = render_md(meta, data["pages"], sections)
        dst.write_text(md, encoding="utf-8")
        scanned = sum(1 for p in data["pages"] if p["scanned"])
        print(
            f"[{cfg['source_id']}] wrote {dst} | sections={len(sections)} | scanned_pages={scanned} | size={len(md)} chars",
            flush=True,
        )


if __name__ == "__main__":
    main()
