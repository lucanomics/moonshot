# AUDIT_REPORT

## Executive summary
- The repository’s active frontend data source is `visa_data.json` loaded by `loadVisaData()` in `index.html`, with API-first and static fallback routing.  
- The app branding repeatedly claims “39 체류자격”, but `visa_data.json` currently contains 56 entries including operational/helper entries (`K-ETA`, `TB-1`, `SCN-*`, `FAQ-*`, `OVS-1`, `NHIS-1`) beyond formal stay-status rows. This is a terminology/data-model mismatch, not an immediate runtime crash.  
- The “입국 전” and “입국 후” tracks are rendered from hardcoded UI blocks + `visa_data.json` category filtering; they are not dynamically sourced from parsed manual passages at runtime.  
- Based on repository PDF-derived manual text (`docs/sajeung-manual.md`, `docs/ceryu-manual.md` generated from bundled PDFs), several displayed procedural claims are too specific without per-status conditions and should be softened.

## Discovered relevant files
- `index.html` (UI text, event handlers, routing/render logic).  
- `visa_data.json` (primary visa/stay dataset).  
- `260414 사증민원 매뉴얼.pdf` (repo root) and duplicate in `docs/`.  
- `260414 체류민원 매뉴얼.pdf` (repo root) and duplicate in `docs/`.  
- `docs/sajeung-manual.md`, `docs/ceryu-manual.md` (PDF extraction outputs).  
- `scripts/rag/extract_pdf.py` (PDF parsing pipeline).  

## Architecture summary (visa/manual logic)
1. `DOMContentLoaded -> loadVisaData()` loads `/api/visas`, fallback `./visa_data.json`.  
2. Track buttons call `startPreEntryTrack()` / `startInKoreaTrack()`.  
3. Pre-entry path: purpose card click -> `showVisaRecommendations(purpose)` -> `VISA_DATA` filtered by category -> cards rendered -> `openDocModal(code,'new')`.  
4. Post-entry path: action card click -> `selectInKoreaAction(actionType)` -> hardcoded explanatory copy + search UI -> `filterInKoreaVisaList()`.  
5. Manual content is referenced conceptually, but this path is not pulling page-scoped manual snippets at render time.

## Discrepancy inventory
1. **Terminology/Data-model mismatch (Medium)**  
   - UI repeatedly asserts “39 체류자격”, while dataset includes 56 mixed records.  
   - Classification: terminology + data issue.

2. **Pre-entry wording mismatch (Low)**  
   - UI heading uses “주한공관 사증 신청”; official flow language is generally “재외공관” for overseas issuance context.  
   - Classification: terminology issue.

3. **Unsupported hardcoded exception example (High)**  
   - Post-entry change track shows fixed claim: “(예: C-3 → D-2 불가)”. Qualification-change permissibility is highly condition-dependent and should not be rendered as universal without specific source citation.  
   - Classification: unsupported claim.

4. **Manual linkage gap (Medium)**  
   - Core track output is not traceably bound to manual section IDs/pages in UI rendering path; content mostly static advisory copy plus JSON snippets.  
   - Classification: rendering/routing traceability issue.

## PDF evidence notes (paraphrased)
- Visa manual includes visa issuance application and COA pathways through overseas Korean missions (`재외공관`) and category-specific required docs.  
- Stay manual governs post-entry services (registration, extension, status changes) with requirements depending on current status, purpose, and attached proof.  
- Therefore, unconditional UI statements about conversion impossibility are risky unless explicitly bounded.

## Severity summary
- High: 1
- Medium: 2
- Low: 1

## Affected files
- `index.html` (primary discrepancies surfaced here).  
- `visa_data.json` (count/model vs branding framing).

## Full audit of required documents by visa/stay qualification

| Code | Name | App behavior (docs fields) | Manual coverage (PDF-derived MD) | Mismatch summary | Severity | Issue type |
|---|---|---|---|---|---|---|
| K-ETA | 전자여행허가 (K-ETA) 종합 가이드 | new:3, ext:2, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| TB-1 | 결핵 고위험 국가 진단서 제출 기준 | new:1, ext:1, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| SCN-1 | 글로벌 의사결정 매트릭스 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| SCN-2 | 실무 변수 체크리스트 | new:2, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| SCN-3 | C-3 (단기) 자격변경 시나리오 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| SCN-4 | F-1-6 (혼인단절) 타이밍 시나리오 | new:1, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| SCN-5 | F-4/H-2 (동포) 제약 시나리오 | new:2, ext:2, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| SCN-6 | 오버스테이 (불법체류) 시나리오 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| OVS-1 | 불법체류다발국가 목록 | new:1, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| NHIS-1 | 국외 체류자 건강보험 면제·감면 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| FAQ-1 | 외국인등록 및 체류지 변경 | new:4, ext:1, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| FAQ-2 | 체류기간 연장·자격 변경 | new:0, ext:3, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| FAQ-3 | 재입국허가 | new:0, ext:4, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| FAQ-4 | 전자팩스·오버스테이·국적 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| VW-1 | 무사증·사증면제 구분 | new:0, ext:0, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; No document lists rendered from JSON; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, missing document, wrong category separation |
| COM-1 | 비자 공통 구비서류·팁 | new:4, ext:1, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| B-1 | 사증면제협정 | new:1, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| B-2 | 관광통과·무사증 | new:2, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| C-3 | 단기방문 | new:8, ext:3, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| C-4 | 단기취업 | new:5, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| D-1 | 문화예술 | new:5, ext:4, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-2 | 유학 | new:4, ext:11, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-3 | 기술연수 | new:4, ext:4, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-4 | 일반연수 | new:4, ext:9, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-4-2K | 한국어연수(K-연수생) | new:8, ext:6, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-7 | 주재 | new:5, ext:10, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-8 | 기업투자 | new:5, ext:7, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-9 | 무역경영 | new:3, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-10 | 구직 | new:4, ext:10, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-1 | 교수 | new:4, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-2 | 회화지도 | new:6, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-3 | 연구 | new:4, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-4 | 기술지도 | new:3, ext:7, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-5 | 전문직업 | new:2, ext:7, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-6 | 예술흥행 | new:4, ext:7, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-7 | 특정활동 | new:5, ext:14, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-8 | 계절근로 | new:4, ext:6, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-9 | 비전문취업 | new:4, ext:9, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| E-10 | 선원취업 | new:3, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-1 | 방문동거 | new:4, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-2 | 거주 | new:4, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-3 | 동반 | new:4, ext:6, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-4 | 재외동포 | new:4, ext:3, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-5 | 영주 | new:4, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| F-6 | 결혼이민 | new:9, ext:15, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| G-1 | 기타(난민등) | new:4, ext:5, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| RF-1 | 난민인정신청 제출서류 안내 | new:7, ext:2, change:absent | none | Non-manual helper/scenario/FAQ entry; not a canonical visa qualification row; Change-of-status requirements are not modeled per-entry | Medium | JSON/source-data issue, categorization, wrong category separation |
| H-1 | 관광취업 | new:4, ext:5, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| H-2 | 방문취업 (신규발급 중단) | new:0, ext:8, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| A-1 | 외교 | new:2, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| A-2 | 공무 | new:2, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| A-3 | 협정 | new:2, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| C-1 | 일시취재 | new:3, ext:0, change:absent | 사증,체류 | Initial docs present but extension docs absent in app data; Change-of-status requirements are not modeled per-entry | Medium | missing document, wrong category separation |
| D-5 | 취재 | new:3, ext:6, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-6 | 종교 | new:3, ext:6, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
| D-4-2K | 기업맞춤형인턴십(K-Trainee) | new:4, ext:2, change:absent | 사증,체류 | Change-of-status requirements are not modeled per-entry | Medium | wrong category separation |
