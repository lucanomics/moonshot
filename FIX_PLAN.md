# FIX_PLAN

## File: `index.html`
1. Replace “주한공관 사증(비자) 신청” with “재외공관 사증(비자) 신청”.  
   - Rationale: align with overseas pre-entry issuance terminology in visa manual.
   - Evidence: visa manual flow language around overseas consular processing.

2. Replace hardcoded example “(예: C-3 → D-2 불가)” with neutral, condition-based caution text.  
   - Rationale: remove potentially unsupported universal claim.
   - Evidence: stay manual treats change-of-status under conditions/doc review.

3. Keep “39” branding unchanged for this patch, but mark as terminology risk in audit report only.  
   - Rationale: large UX/content ripple; conservative fix scope this round.

## File: `AUDIT_REPORT.md`
- Add evidence-based discrepancy log and classifications.

## File: `FIX_PLAN.md`
- Track minimal safe edit plan before patch execution.

## Required document accuracy remediation plan

1. **Files to change**
   - `visa_data.json`: introduce explicit stage-separated fields (`initial_issue_docs`, `extension_docs`, `change_status_docs`) while preserving legacy keys for compatibility.
   - `index.html`: render stage tabs strictly by stage field and display official document labels first, with helper text secondary.
   - `docs/sajeung-manual.md`, `docs/ceryu-manual.md` (reference only): use exact manual wording as authoritative labels during curation.

2. **Data fields to correct/split**
   - Split `newReqDocs` into visa-issuance vs in-country initial registration where currently blended.
   - Keep `extReqDocs` but add condition metadata (`conditional`, `substitute_allowed`, `applies_to_subcodes`).
   - Add per-code `change_status_docs` (currently absent across searchable entries).

3. **UI labels to update**
   - Show official document names (e.g., `사증발급신청서(별지 제17호 서식)`) as primary labels.
   - Move simplified helper wording into expandable notes; do not replace official labels.

4. **Stage separation**
   - Enforce explicit separation for `신규 발급/신청`, `체류기간 연장`, `체류자격 변경`.
   - If a stage is unsupported for a code, render `매뉴얼에서 해당 단계의 일반요건을 확인 필요` rather than reusing another stage list.

5. **Safe immediate fixes vs manual review**
   - **Safe immediate**: terminology/UI warnings, non-canonical helper rows clearly tagged as `가이드/시나리오` not visa qualification.
   - **Manual review required**: every per-code official document list normalization against the two manuals (especially subcode-dependent conditions and substitution clauses).
