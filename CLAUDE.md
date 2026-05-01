# CLAUDE.md — Paradiso Operating Rules

> This file governs all Claude Code sessions working on the Paradiso repository.
> Read this before taking any action. Rules here override defaults.

---

## 1. Project Identity

- **Service name**: Paradiso (never "Paradiso 39" — 39 is a copy figure, not part of the brand)
- **Domain**: AI-powered Korean immigration, visa, and residence information platform
- **Target users**: Foreigners, students, workers, artists, researchers, and migrants navigating Korean visa and residence procedures
- **Nature of service**: Administrative guidance tool — not legal advice, not an official government channel
- **Active competitions**:
  1. 제2회 법령데이터 활용 아이디어 공모전 (법제처) — **top priority**
  2. 2026 국민공공외교사업 — second priority
  3. 제4회 문화체육관광 인공지능·데이터 활용 공모전 — third priority
- **Strategy reference**: `docs/CONTEST_STRATEGY.md`

---

## 2. Source Hierarchy

Treat sources in strict descending order of authority. Never invert this order.

| Tier | Source | Role |
|------|--------|------|
| 1 (highest) | `260414 사증민원 매뉴얼.pdf`, `260414 체류민원 매뉴얼.pdf` | Primary source of truth for all visa and residence procedure data |
| 2 | `docs/sajeung-manual.md`, `docs/ceryu-manual.md` | Extracted text from Tier 1 PDFs; use for fast lookup, verify against Tier 1 for any disputed passage |
| 3 | `docs/2026_MANUAL_SOURCE_AUDIT_REPORT.md`, `AUDIT_REPORT.md`, `FIX_PLAN.md` | Reference documents only — record past findings, not a source for new claims |
| 4 (lowest) | `visa_data.json`, `index.html`, `ai.html` | **Audit targets, not truth** — these files are validated against Tier 1–2, never used to justify data claims |

Rules:
- Any proposed data change must cite a specific Tier 1 page or section.
- Tier 3 documents record what was found in prior audits; they do not authorize new changes.
- Tier 4 files are never used as evidence that a procedure or requirement is correct.

---

## 3. Safety Rules

### 3.1 No Legal Advice
- Never state that a user "will receive" or "is eligible for" a visa or permit.
- Never guarantee approval, processing time, or outcome.
- All guidance must be framed as: "According to [source], the general requirement is…"
- Every procedural answer must end with a referral to 1345 or the relevant 출입국·외국인청.

### 3.2 No Permission or Approval Guarantees
- Do not assert that possession of a document guarantees issuance.
- Do not assert that meeting stated requirements guarantees a positive decision.
- Discretionary officer judgment is always in scope; never hide this.

### 3.3 No Broad Refactors
- Do not refactor code, rename functions, or restructure files unless the user explicitly requests it for a specific task.
- Bug fixes and data corrections must be scoped to the minimum change needed.
- Do not clean up unrelated code while fixing something else.

### 3.4 No UI Redesign Without Explicit Instruction
- Do not alter layout, color tokens, CSS variables, or component structure unless instructed.
- Preserve all existing CSS variable names (`:root` tokens) — values may be adjusted only on direct instruction.
- Preserve the sunrise canvas animation (`#starCanvas`, `PHASES`).
- Preserve the anagram motion classes (`.al .src .tgt`).

### 3.5 No Automatic Batch 2/3 Data Normalization
- PR #56 applied Batch 1 only (RF-1 category fix, confirmed).
- Batch 2 and Batch 3 corrections from the audit remain **deferred**.
- Do not apply Batch 2/3 changes automatically or bundle them into unrelated PRs.
- Any Batch 2/3 fix requires explicit user instruction and a separate branch.

---

## 4. Tool and Model Routing

| Task | Recommended model/tool |
|------|------------------------|
| Long manual interpretation, multi-page PDF analysis, competition strategy | **Claude Opus** |
| Small local edits, single-file patches, JSON field corrections | **Claude Sonnet** |
| PR patches, automated validation, CI-style checks | **Codex** |
| External judge-style review, independent second opinion | **Gemini** |

Notes:
- Switch models explicitly via `/model` before starting a task if the default is mismatched.
- Do not use a lightweight model for PDF interpretation — Tier 1 PDF passages require careful reading.
- Do not use a heavy model for trivial one-line edits — Sonnet is sufficient and faster.

---

## 5. Branch and PR Discipline

- **One task per branch** — do not combine unrelated changes.
- **Branch naming**: use descriptive lowercase-hyphenated names (e.g., `fix/rf1-category`, `feat/en-locale-toggle`).
- **Small PRs** — each PR should be reviewable in under 10 minutes. If a change is large, split it.
- **No force push** — never run `git push --force` or `git push --force-with-lease` without explicit user instruction.
- **No merge without user confirmation** — Claude Code must never merge a PR autonomously. Always stop and ask.
- **No amending published commits** — create a new commit instead of amending after a push.
- **Commit messages**: concise present-tense imperative, cite the specific file and change (e.g., `fix: set RF-1 cat to scn per 체류매뉴얼 p.42`).

---

## 6. Validation Checklist

Run these checks after any data or code change, before reporting work as done.

```bash
# 1. JSON syntax validity
python3 -m json.tool visa_data.json > /dev/null && echo "JSON OK"

# 2. Diff size sanity
git diff --stat

# 3. Whitespace and conflict markers
git diff --check

# 4. Brand regression: "Paradiso 39" must not appear as brand copy
grep -rn "Paradiso 39" index.html ai.html visa_data.json && echo "REGRESSION: brand copy" || echo "brand OK"
```

When `index.html` changes:
- Run the above plus a manual smoke test: open the page in a browser, verify search, category tabs, modal open/close, and footer disclaimer are intact.
- Do not mark UI work complete without a live browser check.

---

## 7. Contest Preparation Priorities

Work should flow in this order when contest preparation and product tasks compete for time:

1. **법령데이터 공모전 (법제처)** — law.go.kr / open.law.go.kr citation integration, source badge on procedure cards, 5-action labeling (사증발급/외국인등록/체류기간연장/체류자격변경/각종신고)
2. **국민공공외교사업** — EN locale toggle, multilingual copy, persona-driven flows, 1345 referral integration
3. **문화체육관광 AI·데이터 공모전** — E-6/E-2/E-7(문화) track separation, cultural/tourism sector user flows

Do not begin lower-priority contest work if higher-priority items are incomplete.

---

## 8. Forbidden Autonomous Actions

Claude Code must **never** do the following without explicit per-action user confirmation:

| Action | Reason |
|--------|--------|
| Merge any pull request | Irreversible shared-state change |
| Rewrite or bulk-normalize `visa_data.json` | Risk of data loss; Batch 2/3 deferred |
| Reformat files that are not part of the current task | Pollutes diffs; hides real changes |
| Invent or infer missing official data | Fabricated data presented as fact violates the source hierarchy |
| Treat uncertain PDF findings as confirmed | A finding is confirmed only when explicitly approved by the user |
| Push to `main` or merge into `main` | Main branch is protected; always go through PR |
| Delete branches or files | Destructive and potentially irreversible |
| Run `git reset --hard`, `git clean -f`, or equivalent | Destructive — destroys working tree without recovery |

---

## Appendix — Key File Map

| File | Purpose |
|------|---------|
| `index.html` | Main single-page frontend (search, catalog, modals) |
| `ai.html` | Paradiso AI chat interface |
| `visa_data.json` | 39-status structured data (audit target) |
| `docs/CONTEST_STRATEGY.md` | Competition positioning and narrative |
| `docs/2026_MANUAL_SOURCE_AUDIT_REPORT.md` | Audit findings from PR #56 |
| `AUDIT_REPORT.md` | Architecture and discrepancy audit |
| `FIX_PLAN.md` | Deferred fix plan (Batch 2/3) |
| `260414 사증민원 매뉴얼.pdf` | Tier 1 source — visa issuance |
| `260414 체류민원 매뉴얼.pdf` | Tier 1 source — residence/registration |
| `docs/sajeung-manual.md` | Tier 2 — extracted visa manual text |
| `docs/ceryu-manual.md` | Tier 2 — extracted residence manual text |
| `moonshot_backend_fastapi.py` | FastAPI backend |
| `moonshot_pipeline_architecture.md` | Architecture reference |
