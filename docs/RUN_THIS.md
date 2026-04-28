# Paradiso 39 — Claude Code 통합 명령 프롬프트

## Claude Code 터미널에 아래 텍스트를 통째로 붙여넣는다

---

```
다음 3개 파일을 순서대로 읽어라.

1. docs/PARADISO39_REFACTOR_PROMPT.md
2. docs/PARADISO39_SCROLL_INTERACTION.md
3. index.html (현재 작업 대상)

읽은 후 아래 순서로 작업해라.

─────────────────────────────────
STEP 0 — 준비
─────────────────────────────────
- index.html → index_backup.html 백업
- 브랜치 생성: git checkout -b improve/scroll-and-a11y

─────────────────────────────────
STEP 1 — 접근성 마무리 (REFACTOR_PROMPT.md 기준)
─────────────────────────────────
아직 미완료된 항목만 처리한다. 이미 구현된 항목은 건드리지 않는다.
확인 방법: index.html에서 직접 검색해서 존재 여부를 먼저 판단하고 보고해라.

체크 대상:
- <img> 태그에 alt 속성 없는 것 → alt="" aria-hidden="true" 추가
- @media (max-width: 768px) .hero-container min-height 조정 여부
- landing-hints 인기 검색 칩 5개 렌더링 여부

─────────────────────────────────
STEP 2 — 스크롤 인터랙션 (SCROLL_INTERACTION.md 기준)
─────────────────────────────────
Phase 1 → 2 → 3 → 4 순서로 전부 구현한다.

절대 건드리지 말 것:
- VISA_DATA, COMMON_NEW, COMMON_EXT, DOC_DICT
- executeSearch, renderResults, clearSearch 함수 시그니처
- starCanvas PHASES 색상값
- anagram-run / launched / searched 클래스 기반 상태 전환
- body.searched .brand-hero/brand-feature/about-me 숨김 처리

─────────────────────────────────
STEP 3 — 자체 검증
─────────────────────────────────
완료 후 아래 항목을 코드에서 직접 확인하고 결과를 ✅/❌ 로 표시해라.

[ ] index_backup.html 존재
[ ] 브랜치 improve/scroll-and-a11y 체크아웃 상태
[ ] IntersectionObserver 코드 존재 (라인 번호 명시)
[ ] [data-reveal] CSS 존재
[ ] [data-stagger] CSS 존재
[ ] prefers-reduced-motion 분기 존재
[ ] .scroll-cue 존재
[ ] .section-divider 존재
[ ] 모든 <img>에 alt 속성 존재
[ ] alert() 호출 0개
[ ] onclick= 인라인 속성 0개
[ ] VISA_DATA 변경 없음 (git diff로 확인)
[ ] executeSearch 함수 시그니처 변경 없음

─────────────────────────────────
STEP 4 — 커밋
─────────────────────────────────
검증 통과 항목만 커밋한다. 실패 항목이 있으면 먼저 수정하고 커밋해라.

git add index.html
git commit -m "feat(scroll): add IntersectionObserver reveal + a11y fixes"
git push origin improve/scroll-and-a11y

커밋 완료 후 Push URL을 나에게 알려라. 내가 GitHub에서 직접 Pull Request를 만들겠다.
```