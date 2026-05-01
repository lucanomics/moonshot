# 2026.3 Manual Source Audit Report (Recreated from Claude local result)

## Scope
This report recreates the already-completed Claude audit output that was previously committed only in Claude's local environment (`6683805`) and not pushed.

- No broad re-audit was rerun.
- Only the single confirmed Batch 1 data fix was applied in this PR.
- Batch 2/3 and structural modeling issues remain deferred.

## Source-of-Truth Manuals Referenced
- `260414 사증민원 매뉴얼.pdf`
- `260414 체류민원 매뉴얼.pdf`

Expected locations noted in the original audit summary:
- `/home/user/moonshot/260414 사증민원 매뉴얼.pdf`
- `/home/user/moonshot/260414 체류민원 매뉴얼.pdf`
- sibling copies under `docs/`

## Method (from recreated Claude summary)
- Direct PDF inspection was performed in the original audit.
- `pdftotext -layout` was used.
- Evidence was inspected directly from PDF contents.

## Applied Change (Batch 1 only)
### F-001
- File: `visa_data.json`
- Entry: `RF-1`
- Change: `cat` value
  - from: `other`
  - to: `scn`

### Rationale
`RF-1` is not a canonical visa/status code. It is a refugee-related submission/document guidance or scenario-style entry. In the manuals, refugee-related procedures map to statuses/processes such as `G-1-5`, `G-1-6`, refugee-related `F-2`, and refugee-family-related `F-1`. Therefore `RF-1` should be classified as a scenario/helper entry, not as a regular `other` visa/status category.

### Expected Product Behavior
This routes `RF-1` through the existing special-scenario CTA flow, instead of presenting it as a normal visit/short-term/other recommendation.

## Confirmed but Deferred (No patch in this PR)
### F-002 / F-003
- Duplicate top-level `D-4-2K`
- `D-4` sub-code `D-4-2K` mislabel (currently `한국어연수`; expected `K-Trainee` per manual evidence)
- Deferred intentionally because rename vs delete requires human product/content decision and accompanying body-text rewrite.

## Batch 2/3 Deferred (No patch in this PR)
- D-4 family naming reconciliation
- manual #38/#39/#40 modeling
- separation of document layers:
  - 사증발급
  - 외국인등록
  - 연장
  - 변경
  - 신고
- per-code document-list normalization
- page/section evidence mapping

## Manual Review Queue (Open)
- F-002/F-003: `D-4-2K` duplicate / sub-code mislabel
- F-007: `D-4-5 한식조리연수` source not found in scanned PDF set
- F-011/F-012: Paradiso v38 footer and internal `docs/PARADISO39_*` prompt files
- Batch 2/3 items listed above

## Notes
This report is a practical reconstruction of the already-completed Claude audit summary and intentionally limits changes to the single high-confidence data fix.
