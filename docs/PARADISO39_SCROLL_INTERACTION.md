# Paradiso 39 — 스크롤 인터랙션 구현 명령서

> 대상 파일: `online_viewer_net__6_.html` (이하 "현재 파일")  
> 목표: 랜딩 상태에서 스크롤 시 brand-hero · brand-feature · about-me 섹션이  
> Figma 시안처럼 인터랙티브하게 진입하는 효과 구현  
> 제약: 단일 HTML 파일 유지 · 외부 JS 라이브러리 추가 금지 · 핵심 기능 보존

---

## 0. 작업 전 필독 (컨텍스트)

### 현재 파일 상태 (1차 점검 완료)

**업그레이드 확인된 항목** — 건드리지 마라:
- `<form role="search">` + `type="search"` (라인 519~528)
- 5개 모달 전체에 `role="dialog" aria-modal="true"` 적용됨
- `data-action` 패턴 29개 + 단일 이벤트 위임 핸들러
- `.toast` 컴포넌트 (alert() 제거 완료)
- `:focus-visible` + `.sr-only` CSS 구현됨
- `ESC 닫기` 핸들러 (라인 1913)
- `brand-hero` / `brand-feature` / `about-me` 3개 섹션 HTML 존재

**미해결 항목 2개** — 이번 작업 대상:
1. `IntersectionObserver` 없음 → 스크롤 인터랙션 미구현
2. `<img>` 태그의 `alt=""` 없음 → 이번 작업에서 함께 처리

### 절대 변경 금지

- `VISA_DATA`, `COMMON_NEW`, `COMMON_EXT`, `DOC_DICT`, `executeSearch`, `renderResults` 등 핵심 검색 로직
- `#starCanvas` 일출 캔버스 + `PHASES` 색상값
- `anagram-run`, `launching`, `searched` 클래스 기반 상태 전환 로직
- `:root` CSS 변수명 (값 조정은 허용, 이름 변경 금지)
- `body.searched .brand-hero`, `body.searched .brand-feature`, `body.searched .about-me` 숨김 처리 — 검색 시 3개 섹션이 사라지는 것은 의도된 동작

---

## 1. Phase 1 — 스크롤 진입 애니메이션 (IntersectionObserver)

### 1.1 CSS — reveal 클래스 정의

`<style>` 블록 내에 아래 CSS를 추가한다.  
`brand-hero`, `brand-feature`, `about-me`의 기존 `display: block` 규칙은 건드리지 않는다.

```css
/* ── Scroll Reveal ─────────────────────────────── */
[data-reveal] {
    opacity: 0;
    transition-property: opacity, transform, filter;
    transition-duration: 0.7s;
    transition-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
    will-change: opacity, transform;
}

[data-reveal="fade-up"] {
    transform: translateY(40px);
}
[data-reveal="fade-left"] {
    transform: translateX(-40px);
}
[data-reveal="fade-right"] {
    transform: translateX(40px);
}
[data-reveal="scale-up"] {
    transform: scale(0.94);
    filter: blur(2px);
}
[data-reveal="fade-down"] {
    transform: translateY(-24px);
}

[data-reveal].revealed {
    opacity: 1;
    transform: none;
    filter: none;
}

/* stagger: 형제 요소 순차 진입 */
[data-stagger] > * {
    opacity: 0;
    transform: translateY(28px);
    transition: opacity 0.55s cubic-bezier(0.22, 1, 0.36, 1),
                transform 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}
[data-stagger] > *.revealed {
    opacity: 1;
    transform: none;
}

/* prefers-reduced-motion: 모션 비활성화 */
@media (prefers-reduced-motion: reduce) {
    [data-reveal],
    [data-stagger] > * {
        opacity: 1 !important;
        transform: none !important;
        filter: none !important;
        transition: none !important;
    }
}
```

### 1.2 HTML — 섹션별 data-reveal 속성 부여

아래 각 요소에 `data-reveal` 또는 `data-stagger` 속성을 추가한다.  
기존 클래스와 다른 속성은 건드리지 않는다.

**brand-hero 섹션 (라인 551~590)**:

```html
<!-- 헤드라인 텍스트 블록 -->
<div class="brand-hero-text" data-reveal="fade-up">
    ...
</div>

<!-- stat 카드 그룹: stagger로 순차 진입 -->
<div class="brand-hero-stats" aria-label="비자 카테고리 통계" data-stagger>
    <div class="stat-card">...</div>
    <div class="stat-card">...</div>
    <div class="stat-card">...</div>
    <div class="stat-card">...</div>
</div>
```

**brand-feature 섹션 (라인 591~627)**:

```html
<!-- 좌측 텍스트 -->
<div class="feature-content" data-reveal="fade-left" data-reveal-delay="0">
    ...
</div>

<!-- 우측 체크리스트 카드 -->
<aside class="feature-checklist" data-reveal="fade-right" data-reveal-delay="150">
    ...
</aside>
```

**about-me 섹션 (라인 628~686)**:

```html
<!-- 섹션 타이틀 -->
<h2 id="aboutMeTitle" class="about-title" data-reveal="fade-up">
    프로젝트 소개
</h2>

<!-- about-me 내부 카드/블록들: stagger 그룹으로 처리 -->
<div class="about-cards" data-stagger>
    <!-- 기존 내부 블록들을 이 div로 감싸거나, 기존 직계 자식에 직접 적용 -->
</div>
```

### 1.3 JS — IntersectionObserver 구현

기존 JS 블록 맨 끝(`</script>` 직전)에 아래 코드를 추가한다.  
기존 함수를 수정하지 않는다.

```js
/* ── Scroll Reveal Engine ─────────────────────────────── */
(function initScrollReveal() {
    // prefers-reduced-motion 감지: 모션 선호 없으면 즉시 reveal
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
        document.querySelectorAll('[data-reveal], [data-stagger] > *').forEach(el => {
            el.classList.add('revealed');
        });
        return;
    }

    // 1) 단일 요소 reveal
    const revealEls = document.querySelectorAll('[data-reveal]');
    const revealObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            const delay = parseInt(el.dataset.revealDelay || '0', 10);
            setTimeout(() => el.classList.add('revealed'), delay);
            revealObs.unobserve(el); // 한 번 진입하면 다시 관찰 안 함
        });
    }, {
        threshold: 0.12,
        rootMargin: '0px 0px -60px 0px'
    });
    revealEls.forEach(el => revealObs.observe(el));

    // 2) stagger 그룹: 자식 요소 순차 진입
    const staggerGroups = document.querySelectorAll('[data-stagger]');
    const staggerObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const children = Array.from(entry.target.children);
            const baseDelay = parseInt(entry.target.dataset.staggerDelay || '80', 10);
            children.forEach((child, i) => {
                setTimeout(() => child.classList.add('revealed'), i * baseDelay);
            });
            staggerObs.unobserve(entry.target);
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px'
    });
    staggerGroups.forEach(group => staggerObs.observe(group));
})();
```

---

## 2. Phase 2 — 섹션별 인터랙션 강화

### 2.1 stat-card — 호버 + 카운트업 애니메이션

stat-card의 숫자(14 / 8 / 7 / 10)를 진입 시 0에서 해당 숫자까지 카운트업.

**HTML**: 각 `.stat-num` 요소에 `data-count="숫자"` 속성 추가.

```html
<div class="stat-num" data-count="14">0</div>
<div class="stat-num" data-count="8">0</div>
<div class="stat-num" data-count="7">0</div>
<div class="stat-num" data-count="10">0</div>
```

**JS**: 위 `initScrollReveal` 함수 내부, staggerObs의 `forEach` 안에 카운트업 트리거 추가.

```js
// stagger 그룹 진입 시 내부 data-count 요소 카운트업
children.forEach((child, i) => {
    setTimeout(() => {
        child.classList.add('revealed');
        // 카운트업 처리
        const countEl = child.querySelector('[data-count]');
        if (countEl) {
            const target = parseInt(countEl.dataset.count, 10);
            let current = 0;
            const step = Math.ceil(target / 20);
            const timer = setInterval(() => {
                current = Math.min(current + step, target);
                countEl.textContent = current;
                if (current >= target) clearInterval(timer);
            }, 40);
        }
    }, i * baseDelay);
});
```

> **주의**: `VISA_DATA` 배열에 카테고리 분류 필드가 있는 경우, `data-count` 값을 JS에서 동적으로 계산해서 주입하는 것을 권장한다. 필드 구조가 불명확하면 하드코딩(14/8/7/10) 유지 + 코드 주석 `/* TODO: VISA_DATA 카테고리 카운트 동적 주입 */` 추가.

### 2.2 feature-checklist 리스트 아이템 — stagger 개별 진입

`.check-list`의 `<li>` 항목들이 순차적으로 왼쪽에서 슬라이드인.

```html
<ul class="check-list" data-stagger data-stagger-delay="100">
    <li>...</li>
    <li>...</li>
    <li>...</li>
    <li>...</li>
</ul>
```

`[data-stagger] > *`는 이미 `fade-up` 트랜지션이 걸려 있으므로 추가 CSS 불필요.

### 2.3 about-me 섹션 — 좌우 교차 진입

about-me 섹션 내 카드/블록들이 홀수는 왼쪽, 짝수는 오른쪽에서 진입.

```css
/* about-me 내부 블록 교차 방향 */
.about-me > *:nth-child(odd)[data-reveal] {
    transform: translateX(-32px);
}
.about-me > *:nth-child(even)[data-reveal] {
    transform: translateX(32px);
}
.about-me > *.revealed {
    transform: none;
    opacity: 1;
}
```

HTML에서 about-me의 직계 자식 블록들에 `data-reveal` 추가:

```html
<section id="aboutMe" class="about-me" aria-labelledby="aboutMeTitle">
    <h2 id="aboutMeTitle" class="about-title" data-reveal="fade-up">프로젝트 소개</h2>
    <div class="about-block about-block-intro" data-reveal>...</div>
    <div class="about-block about-block-features" data-reveal>...</div>
    <div class="about-block about-block-disclaimer" data-reveal>...</div>
</section>
```

---

## 3. Phase 3 — 섹션 간 구분선 + 스크롤 안내 UX

### 3.1 hero → brand-hero 전환 시각 안내

현재 100vh hero 아래에 brand-hero가 붙는데, 스크롤 유도 장치가 없음.  
hero 하단에 스크롤 유도 화살표 추가.

```html
<!-- .hero-container 내부 맨 마지막, .landing-hints 아래 -->
<div class="scroll-cue" aria-label="아래로 스크롤" id="scrollCue">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" 
         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
         aria-hidden="true">
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
</div>
```

```css
.scroll-cue {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    color: var(--t3);
    opacity: 0.6;
    cursor: pointer;
    transition: opacity 0.3s;
    animation: scrollBounce 2s ease-in-out infinite;
    z-index: 20;
}
.scroll-cue:hover { opacity: 1; }
body.searched .scroll-cue { display: none; }

@keyframes scrollBounce {
    0%, 100% { transform: translateX(-50%) translateY(0); }
    50% { transform: translateX(-50%) translateY(8px); }
}
```

```js
// 스크롤 시 scroll-cue 페이드 아웃
document.getElementById('scrollCue')?.addEventListener('click', () => {
    document.getElementById('brandHero')?.scrollIntoView({ behavior: 'smooth' });
});
window.addEventListener('scroll', () => {
    const cue = document.getElementById('scrollCue');
    if (!cue) return;
    cue.style.opacity = window.scrollY > 60 ? '0' : '0.6';
}, { passive: true });
```

### 3.2 섹션 간 구분

brand-hero / brand-feature / about-me 사이에 시각적 구분선 추가.

```css
.section-divider {
    width: 100%;
    max-width: 1160px;
    margin: 0 auto;
    height: 1px;
    background: linear-gradient(
        to right,
        transparent,
        var(--bd),
        transparent
    );
    opacity: 0.5;
}
```

```html
<!-- brand-hero 섹션 다음에 삽입 -->
<div class="section-divider" aria-hidden="true"></div>

<!-- brand-feature 섹션 다음에 삽입 -->
<div class="section-divider" aria-hidden="true"></div>
```

---

## 4. Phase 4 — alt 속성 처리 (미해결 항목)

현재 파일에 `<img>` 태그가 존재하지만 `alt` 속성이 0개임.  
(이미지가 순수 장식용이라면 `alt=""` 빈 값, 의미 있는 이미지라면 설명 문자열)

1. 파일 내 모든 `<img>` 태그를 찾아 목록화.
2. 각 이미지의 역할을 판단:
   - 장식용(배경, 무드 이미지): `alt="" role="presentation"` 또는 `aria-hidden="true"` 추가
   - 정보 전달용(지도, 다이어그램): 한국어 설명 문자열 작성
3. 현재 파일에서는 brand-feature의 우측 이미지(청록 물방울 무늬 이미지)가 장식용이므로:
   ```html
   <img alt="" aria-hidden="true" class="feature-img" ...>
   ```

---

## 5. Phase 5 — 검증 체크리스트

작업 완료 후 항목별로 확인. 미통과 시 수정 후 재검증.

```
□ IntersectionObserver 구현됨 (devtools > Elements > brand-hero 스크롤 시 .revealed 클래스 추가 확인)
□ brand-hero .brand-hero-text → fade-up 진입 확인
□ brand-hero .brand-hero-stats → stat-card 4개 순차 stagger 진입 확인
□ stat-card 숫자 카운트업 0 → 14/8/7/10 확인
□ brand-feature .feature-content → 왼쪽 진입, .feature-checklist → 오른쪽 진입 확인
□ check-list <li> 4개 순차 stagger 진입 확인
□ about-me 섹션 블록 홀수/짝수 교차 방향 진입 확인
□ 스크롤 유도 화살표(.scroll-cue) 표시 + 클릭 시 brand-hero로 스크롤 확인
□ body.searched 상태에서 .scroll-cue hidden 확인
□ prefers-reduced-motion: reduce 환경에서 모든 요소가 즉시 표시됨 (transition 없이)
□ 핵심 검색 기능 정상 작동 (executeSearch → 결과 렌더링 → brand-hero 숨김)
□ 모달 5개 ESC 닫기, focus trap 정상 작동
□ 모바일 360px에서 stagger 애니메이션 정상 작동 (레이아웃 깨짐 없음)
□ Lighthouse Performance 점수 저하 없음 (IntersectionObserver는 rAF 대비 성능 부담 낮음)
□ 모든 <img>에 alt 속성 존재 (alt="" 포함)
```

---

## 6. 작업 순서 권장

```
1. 백업: online_viewer_net__6_.html → online_viewer_backup.html
2. Phase 1.1 CSS 추가 → Phase 1.2 HTML data-reveal 부여 → Phase 1.3 JS 추가
3. 브라우저에서 스크롤 테스트 (Chrome DevTools > Network 탭에서 throttle 걸어 느리게 확인)
4. Phase 2 — 카운트업, stagger 강화
5. Phase 3 — 스크롤 유도 + 구분선
6. Phase 4 — alt 속성
7. Phase 5 검증
8. Git commit:
   - feat(scroll): add IntersectionObserver reveal engine [code-only]
   - feat(ux): add scroll-cue + section dividers [code-only]
   - fix(a11y): add alt attributes to all img tags [code-only]
```

---

## 7. 막혔을 때

**Q: IntersectionObserver가 brand-hero에서 동작 안 함**  
→ `body.searched .brand-hero { display: none }`이 초기에도 적용되는지 확인.  
→ 현재 파일은 랜딩 상태에서 `display: block`이 명시되어 있으므로 정상이어야 함.  
→ 개발자 도구에서 직접 `.brand-hero`의 computed `display` 확인.

**Q: stagger 대상 자식 요소가 무엇인지 불확실**  
→ `.brand-hero-stats`의 직계 자식은 `.stat-card` 4개.  
→ `.check-list`의 직계 자식은 `<li>` 4개.  
→ `data-stagger`는 직계 자식(`children`)에만 작용하므로 손자 요소는 별도 처리 불필요.

**Q: 검색 후 brand-hero가 다시 나타나지 않는 현상**  
→ `body.searched` 클래스 제거 시점(clearSearch 함수)과 `.revealed` 클래스 상태 충돌 가능.  
→ clearSearch 함수에서 brand-hero, brand-feature, about-me의 `.revealed` 클래스를 제거하고,  
   IntersectionObserver를 다시 등록하는 `resetReveal()` 함수 추가:
```js
function resetReveal() {
    document.querySelectorAll('[data-reveal].revealed').forEach(el => {
        el.classList.remove('revealed');
        revealObs.observe(el);
    });
    document.querySelectorAll('[data-stagger] > *.revealed').forEach(el => {
        el.classList.remove('revealed');
    });
    document.querySelectorAll('[data-stagger]').forEach(group => {
        staggerObs.observe(group);
    });
}
// clearSearch() 함수 내에서 resetReveal() 호출
```
→ 단, `initScrollReveal` 내부에서 `revealObs`, `staggerObs`를 클로저 외부(모듈 스코프)로 노출해야 `resetReveal()`에서 접근 가능. `let revealObs, staggerObs;`로 외부 선언 후 내부에서 할당.

**Q: 카운트업 숫자가 검색 후 초기화 안 됨**  
→ clearSearch 후 `data-count` 요소의 `textContent`를 `'0'`으로 리셋:
```js
document.querySelectorAll('[data-count]').forEach(el => {
    el.textContent = '0';
});
```

---

> **최종 원칙**: 스크롤 인터랙션은 사용자가 "이 사이트 살아있구나"를 느끼게 하는 장치다.  
> 과하면 산만하다. **진입 딜레이 합계가 400ms를 넘지 않도록** stagger 간격을 조절해라.  
> prefers-reduced-motion 대응 없으면 출시 불가 — 이건 선택이 아니라 기본이다.