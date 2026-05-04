# CONTEST_DEMO_READINESS_CHECKLIST

## 1) Current visual phase summary
- **Phase 1**: Cinematic landing hero
- **Phase 2**: Action cards and visa manual cards
- **Phase 3**: Search surface and keyword chips
- **Phase 4**: Local Unsplash hero image assets
- **Phase 5**: Searched result cards
- **Phase 6**: Mobile/tablet responsive polish

---

## 2) Demo route (judge walkthrough)
1. Open the landing page.
2. Introduce the hero and main value proposition.
3. Click **direct search**.
4. Search a common keyword (e.g., visa type or use-case keyword).
5. Show searched results.
6. Expand one result card.
7. Open the source/document trigger (if available in the result).
8. Reset to landing.
9. Open the job code modal.
10. Open the jurisdiction modal.
11. Switch to a mobile viewport and show responsive behavior.

---

## 3) Screenshot checklist
Capture all of the following:
- Desktop landing hero
- Direct search open state
- Autocomplete state
- Search results state
- Expanded result card
- Job code modal
- Jurisdiction modal
- Mobile landing
- Mobile searched results

---

## 4) Smoke test checklist
- [ ] Landing loads
- [ ] Direct search opens/closes
- [ ] X button works
- [ ] Keyword chip search works
- [ ] Search query works
- [ ] Results render
- [ ] Result expand/collapse works
- [ ] Reset to landing works
- [ ] Job code modal opens
- [ ] Jurisdiction modal opens
- [ ] AI entry/modal works if present
- [ ] Mobile 390px: no horizontal scroll
- [ ] Tablet 768px: layout stable
- [ ] Hero image loads locally
- [ ] No external image request required
- [ ] debugSearch panel appears only with `?debugSearch=1` (or `#debugSearch`)

---

## 5) Regression guard checklist (run before demo lock)
```bash
git status --short
grep -n "landing-main\|landing-evidence-panel\|근거 확인 흐름" index.html || true
grep -n "SEARCH_DEBUG_ENABLED\|debugSearchState\|setDirectSearchToggleState\|직접 검색 닫기" index.html
grep -n "assets/hero/ws-chae--jVX4mW1Uac-unsplash.jpg" index.html
scripts/check_repo.sh
git diff --check
git diff --stat
```

---

## 6) debugSearch decision (Phase 7)
- Keep `debugSearch` temporarily for final QA because it is gated behind `?debugSearch=1` or `#debugSearch`.
- Do **not** remove it until final contest screenshots and smoke testing are complete.
- If desired, follow up with a cleanup PR after contest/demo lock to remove debug-only instrumentation.

---

## 7) Image attribution reminder
Reference:
- `docs/design/IMAGE_ATTRIBUTIONS.md`

Reminder:
- Verify exact Unsplash source URLs and license notes before final public deployment.
