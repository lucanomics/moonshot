# Paradiso 39 — Claude Code 작업 명령서

> 대상 파일: `index__22_.html` (또는 현재 GitHub Pages에 배포된 메인 HTML)  
> 작업 범위: 접근성·시맨틱 마크업 리팩토링 + Figma 섹션 2개 vanilla 번역 추가  
> 진행 방식: 단일 HTML 파일 유지(React 마이그레이션 금지) · CSS 변수 기반 통일 · 모든 변경 사실 검증 가능

---

## 0. 컨텍스트 (Claude Code가 먼저 읽을 것)

이 프로젝트는 한국 비자 39종을 검색하는 단일 페이지 정적 사이트다. GitHub Pages에서 호스팅 중이며 React 빌드 파이프라인이 없다. **모든 작업은 단일 HTML 파일에서 끝나야 한다.** 외부 의존성 추가 금지(Tailwind CDN 추가 금지, React 추가 금지, 빌드 도구 추가 금지).

### 보존해야 할 자산 (절대 변경 금지)

- `:root` CSS 변수 토큰(라인 14~55)의 **변수명** — 값은 조정 가능하나 이름은 그대로 유지
- 일출 캔버스 애니메이션 `#starCanvas`와 `PHASES` 색상값 (라인 917~926)
- 39개 비자 데이터 처리 로직 — `VISA_DATA`, `COMMON_NEW`, `COMMON_EXT`, `DOC_DICT` (라인 834~894)
- 애너그램 모션 클래스 `.al .src .tgt` (라인 572)
- 직종코드 검색·관할관서 조회·AI 모달 카피 문구

### 절대 추가하지 말 것

- "About us", "Call to action", "A really compelling headline" 같은 영문 SaaS placeholder 문구
- 의미 없는 그라디언트 배경 박스
- Device frame mockup 이미지 (Figma export에 있던 922×599 박스)
- 카드 남발 — 새로운 카드 컴포넌트는 비자 결과 표시에만 사용

---

## 1. Phase 1 — 접근성·시맨틱 리팩토링 (최우선)

### 1.1 검색 폼 정상화

**현재 상태 (라인 577~588)**: `<div class="search-wrap">` > `<div class="sbar">` 안에 `<input type="text">` + `<button onclick="...">` 구조. `<form>` 없음, `<label>` 없음, `aria-label` 없음.

**작업 지시**:
1. `<div class="search-wrap" id="search-wrap">`를 `<form class="search-wrap" id="searchForm" role="search">`으로 교체
2. `<input type="text" id="q">`를 `<input type="search" id="q" aria-label="비자 자격 및 키워드 검색">`로 변경
3. `<button class="xb" id="xb" onclick="clearSearch()">`을 `<button class="xb" id="xb" type="button" aria-label="검색어 지우기" data-action="clear-search">`로 변경
4. `<button class="sbar-go" onclick="executeSearch()" title="검색" disabled>`를 `<button class="sbar-go" type="submit" aria-label="검색" disabled>`으로 변경
5. JS 영역에서 form submit 핸들러 추가:
   ```js
   document.getElementById('searchForm').addEventListener('submit', (e) => {
       e.preventDefault();
       executeSearch();
   });
   ```
6. `clearSearch` 버튼은 위 5번 핸들러와 별도로 `data-action="clear-search"` 위임 처리

### 1.2 시맨틱 헤딩 + 랜드마크 추가

**현재 상태**: 전체 문서에 `<h1>` `<h2>` `<h3>` `<main>` `<nav>` `<header>` `<section>` 모두 0회 등장.

**작업 지시**:
1. 라인 510 `<body>` 직후에 다음 구조 도입:
   - `<header role="banner">`로 라인 514 `#topCtrls` 감싸기
   - 라인 529 `<div class="hero-container" id="hero">`를 `<header class="hero-container" id="hero">`로 변경
   - 라인 642 `<div class="results-area">`를 `<main id="mainContent" class="results-area">`로 변경 (하나의 `<main>`만 존재해야 함)
2. 라인 572 `.logo-brand` `<span>`을 `<h1 class="logo-brand">`로 승격. 단일 H1 보장.
3. 5개 모달의 `.modal-header > span` 안의 텍스트를 `<h2 id="aiModalTitle">` 등으로 교체:
   - 라인 650 → `<h2 id="aiModalTitle" class="modal-title">`
   - 라인 682 → `<h2 id="jobCodeModalTitle" class="modal-title">`
   - 라인 723 → `<h2 id="jurisdictionModalTitle" class="modal-title">`
   - 라인 790 → `<h2 id="docModalTitle" class="modal-title">`
   - 라인 803 → `<h2 id="faqModalTitle" class="modal-title">`
4. `.modal-title` CSS 클래스를 추가하여 기존 `.modal-header span`의 시각 스타일 복제 (font-size, font-weight, margin 동일)

### 1.3 모달 ARIA 속성

**작업 지시**:
1. 5개 `.modal-overlay`에 다음 속성 추가:
   - `role="dialog" aria-modal="true" aria-labelledby="해당 H2의 ID"`
2. 모든 `.modal-close` 버튼에 `aria-label="닫기"` 추가
3. `×`와 `✕` 기호 혼용을 `✕`로 통일 (라인 651, 683, 724, 791, 804)
4. `onclick="closeJobCodeModal()"` (683), `onclick="closeJurisdictionModal()"` (724) 패턴을 `data-action="close-jobcode-modal"`, `data-action="close-jurisdiction-modal"` 패턴으로 통일하여 다른 모달과 일치
5. JS에 모달 키보드 처리 추가:
   ```js
   // ESC 닫기
   document.addEventListener('keydown', (e) => {
       if (e.key === 'Escape') {
           document.querySelectorAll('.modal-overlay.open').forEach(m => {
               m.classList.remove('open');
           });
       }
   });
   // focus trap + 트리거 복원은 별도 함수로 구현
   ```
6. 모달 open 함수에 첫 focusable 요소로 포커스 이동 로직 추가, close 시 트리거 요소로 복원

### 1.4 폼 컨트롤 라벨 + focus 시각화

**작업 지시**:
1. 다음 6개 입력 컨트롤에 라벨 추가:
   - `#q` (라인 580) → `aria-label="비자 자격 및 키워드 검색"` (1.1에서 처리됨)
   - `#citySearch` (라인 522) → `aria-label="도시 이름 검색"`
   - `#aiInput` (라인 655) → 직전에 `<label for="aiInput" class="sr-only">상황 입력</label>` 추가
   - `#jcSearchInput` (라인 687) → `aria-label="업종 또는 직종 검색"`
   - `#jurSido` (라인 731) → `aria-label="시·도 선택"`
   - `#jurSigungu` (라인 734) → `aria-label="시·군·구 선택"`
2. 시각적으로 숨긴 라벨용 CSS 추가:
   ```css
   .sr-only {
       position: absolute;
       width: 1px;
       height: 1px;
       padding: 0;
       margin: -1px;
       overflow: hidden;
       clip: rect(0, 0, 0, 0);
       white-space: nowrap;
       border: 0;
   }
   ```
3. 글로벌 focus 시각화 추가:
   ```css
   :focus-visible {
       outline: 2px solid var(--color-accent);
       outline-offset: 2px;
       border-radius: 4px;
   }
   button:focus-visible, a:focus-visible, input:focus-visible,
   textarea:focus-visible, select:focus-visible {
       outline: 2px solid var(--color-accent);
       outline-offset: 2px;
   }
   ```
4. 기존 `outline: none` 규칙 중 입력 컨트롤(`input`, `textarea`, `select`) 대상은 `:focus-visible` 발동 시 복원되도록 정리. 라인 447 `.jc-search-input`, 488 `.jur-select`의 `outline: none` 유지(이미 `:focus`에서 box-shadow로 시각화) 하되 `:focus-visible`이 우선되도록 specificity 조정

### 1.5 모바일 첫 화면 정리

**현재 상태 (라인 78)**: `.hero-container { min-height: 100vh; }`

**작업 지시**:
1. 모바일 미디어 쿼리(라인 426~435)에 추가:
   ```css
   @media (max-width: 768px) {
       .hero-container:not(.searched .hero-container) {
           min-height: auto;
           padding: 3rem 1rem 1.5rem;
       }
   }
   ```
2. 라인 514 `#topCtrls` 인라인 스타일을 `.top-ctrls` 클래스로 분리하여 `<head>` 메인 `<style>`로 이동
3. `@media (max-width: 640px) #topCtrls`에서 `#cityBtnLabel`을 `display: none`, 테마 버튼 텍스트 "테마 변경"을 `display: none`으로 처리(아이콘 `◐`만 노출)
4. `landingHints` 컨테이너에 기본 인기 검색 칩 5개를 JS에서 렌더링:
   - 라벨: `D-2 유학`, `E-7 특정활동`, `F-6 결혼이민`, `C-3-9 단기방문`, `F-4 재외동포`
   - 클릭 시 해당 키워드를 `#q`에 채우고 `executeSearch()` 호출
   - 칩 클래스명: `.hint-chip` 신설, 기존 `.cb` 스타일 참고하여 시각 일관성 유지

### 1.6 인라인 스타일 + onclick 정리

**작업 지시**:
1. 라인 597~631에 본문 한가운데 박힌 `<style>` 블록을 `<head>` 메인 `<style>`로 이동
2. 다음 라인의 인라인 `style="..."`을 클래스로 분리:
   - 라인 514 `#topCtrls` → `.top-ctrls`
   - 라인 516 `#cityBtn` → `.city-btn`
   - 라인 521 `#cityMenu` → `.city-menu`
   - 라인 526 `#mainThemeBtn` → `.theme-btn`
   - 라인 691 → `.jc-ai-search-row`
   - 라인 728~729 → `.jur-label-accent`, `.jur-sub-margin`
3. 모든 `onclick="..."` 속성(21회)을 `data-action="..."` 패턴으로 통일. 단일 위임 핸들러 추가:
   ```js
   document.addEventListener('click', (e) => {
       const action = e.target.closest('[data-action]')?.dataset.action;
       if (!action) return;
       const handlers = {
           'clear-search': clearSearch,
           'close-ai-modal': () => closeModal('aiModalOverlay'),
           'close-jobcode-modal': closeJobCodeModal,
           'close-jurisdiction-modal': closeJurisdictionModal,
           'close-doc-modal': () => closeModal('docModalOverlay'),
           'close-faq-modal': () => closeModal('faqModalOverlay'),
           // ... 기타
       };
       handlers[action]?.(e);
   });
   ```
4. 하드코딩된 색상값을 CSS 변수로 통일:
   - `#dc2626` (라인 457, 494, 1520, 1675 등) → `var(--color-error)`
   - `#ef4444` (라인 1660 등) → `var(--color-error)`
   - `#10b981` (라인 466) → `var(--color-success)`

### 1.7 alert() 제거

**현재 상태 (라인 2224)**: `alert("⚠ [경고] 해당 시나리오 검색 결과는...")` 사용.

**작업 지시**:
1. `alert()`를 토스트 컴포넌트로 교체:
   ```js
   function showToast(message, type = 'warning') {
       const toast = document.createElement('div');
       toast.className = `toast toast-${type}`;
       toast.setAttribute('role', 'status');
       toast.setAttribute('aria-live', 'polite');
       toast.textContent = message;
       document.body.appendChild(toast);
       setTimeout(() => toast.classList.add('show'), 10);
       setTimeout(() => {
           toast.classList.remove('show');
           setTimeout(() => toast.remove(), 300);
       }, 4000);
   }
   ```
2. CSS:
   ```css
   .toast {
       position: fixed;
       bottom: 5rem;
       left: 50%;
       transform: translateX(-50%) translateY(20px);
       background: var(--color-surface-dark, #0B2A24);
       color: var(--color-surface, #F4EDDC);
       padding: 0.9rem 1.4rem;
       border-radius: var(--radius-md);
       box-shadow: var(--shD);
       opacity: 0;
       transition: opacity 0.3s, transform 0.3s;
       z-index: 2000;
       max-width: 90vw;
       font-size: 0.88rem;
       line-height: 1.5;
   }
   .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
   .toast-warning { border-left: 3px solid var(--color-warning); }
   ```

---

## 2. Phase 2 — Figma Hero 섹션 vanilla 번역 추가

### 2.1 배치 위치

**규칙**:
- 기존 hero(`#hero`, 로고 + 검색창)는 그대로 유지
- Figma Hero를 **검색 후 스크롤 영역**(`<main id="mainContent">` 내부)에 추가
- 단, `body.searched` 상태일 때만 `display: none` 처리하여 검색 결과와 충돌 방지
- 즉, **랜딩 상태**(검색 전)에서만 노출되는 보조 섹션

배치 순서:
```
<header id="hero"> ... 기존 로고 + 검색창 + landing-hints ... </header>
<main id="mainContent">
    <section id="brandHero" class="brand-hero">  ← Figma Hero 번역본 (NEW)
    <section id="brandFeature" class="brand-feature">  ← Figma Feature 번역본 (NEW)
    <div class="qf" id="qf"></div>  ← 기존
    <div class="rlist" id="rlist"></div>  ← 기존
</main>
```

CSS 가시성 제어:
```css
.brand-hero, .brand-feature {
    display: block;
    transition: opacity 0.4s;
}
body.searched .brand-hero,
body.searched .brand-feature {
    display: none;
}
```

### 2.2 Hero 섹션 vanilla 번역

**원본 React 구조**: Hero1 = 배경 이미지 + h1 텍스트 2줄 + 버튼 2개(Primary "About us" / Secondary) + Device frame 이미지

**번역 결정사항**:
- 배경 이미지(`imgHero1`)는 **사용하지 않음**. 일출 캔버스 `#starCanvas`가 이미 전역 배경이므로 중복.
- Device frame 이미지(`imgDeviceFrame`)는 **사용하지 않음**. 한국 행정 서비스에 디바이스 mockup은 부적절. 대체로 **39개 비자 카테고리 통계 위젯**(예: 취업/유학/거주/방문 4개 카테고리 카운트)을 표시.
- "About us" → "서비스 소개" / "About"
- Secondary 버튼 → "1345 안내" / "1345 Hotline" (외국인종합안내센터 직통)
- h1 카피 → "복잡한 체류 정보," / "단 하나의 플랫폼에서." (이미 한국어, 영문 부제 추가)

**HTML 구조**:
```html
<section id="brandHero" class="brand-hero" aria-labelledby="brandHeroTitle">
    <div class="brand-hero-text">
        <h2 id="brandHeroTitle" class="brand-hero-headline">
            복잡한 체류 정보,<br>
            단 하나의 플랫폼에서.
        </h2>
        <p class="brand-hero-subtitle" lang="en">
            Korea's 39 visa categories. Unified.
        </p>
        <div class="brand-hero-buttons">
            <a href="#about" class="btn-primary">
                <span>서비스 소개</span>
                <span class="btn-en" lang="en">About</span>
            </a>
            <a href="tel:1345" class="btn-secondary">
                <span>1345 직접 문의</span>
                <span class="btn-en" lang="en">1345 Hotline</span>
            </a>
        </div>
    </div>
    <div class="brand-hero-stats" aria-label="비자 카테고리 통계">
        <div class="stat-card">
            <div class="stat-num">14</div>
            <div class="stat-label">취업·전문직<br><span lang="en">Employment</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-num">8</div>
            <div class="stat-label">유학·연수<br><span lang="en">Study</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-num">7</div>
            <div class="stat-label">거주·결혼<br><span lang="en">Residence</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-num">10</div>
            <div class="stat-label">방문·기타<br><span lang="en">Visit & Other</span></div>
        </div>
    </div>
</section>
```

> **주의**: 위 카테고리별 숫자(14/8/7/10 = 39)는 임시값이다. 실제 `VISA_DATA` 배열을 기반으로 카테고리 분류 후 카운트해서 동적 렌더링하도록 JS 작성. 카테고리 분류 기준이 데이터에 없다면 임시값을 그대로 두되 코드 주석으로 `TODO: VISA_DATA 카테고리 분류 후 동적 카운트` 명시.

**CSS** (Tailwind 클래스 → CSS 변수 기반 번역):
```css
.brand-hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4rem;
    padding: 6rem 2rem 4rem;
    max-width: 1160px;
    margin: 0 auto;
    text-align: center;
}
.brand-hero-text {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
}
.brand-hero-headline {
    font-family: var(--ff-display);
    font-size: clamp(2rem, 5vw, 4rem);
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.02em;
    color: var(--color-primary-ink);
    margin: 0;
}
.brand-hero-subtitle {
    font-family: var(--ff-display);
    font-size: 1rem;
    color: var(--color-text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.brand-hero-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 1rem;
    justify-content: center;
}
.btn-primary, .btn-secondary {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 0.15rem;
    padding: 0.85rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 700;
    font-size: 1rem;
    text-decoration: none;
    transition: all 0.2s;
    cursor: pointer;
    line-height: 1.2;
}
.btn-primary {
    background: var(--color-primary);
    color: #fff;
    border: 2px solid var(--color-primary);
}
.btn-primary:hover {
    background: var(--color-primary-ink);
    border-color: var(--color-primary-ink);
}
.btn-secondary {
    background: transparent;
    color: var(--color-text);
    border: 2px solid var(--color-border);
}
.btn-secondary:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
}
.btn-en {
    font-size: 0.7rem;
    font-weight: 500;
    opacity: 0.8;
    letter-spacing: 0.05em;
}
.brand-hero-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    width: 100%;
    max-width: 720px;
}
.stat-card {
    background: var(--bg1);
    border: 1px solid var(--bd);
    border-radius: var(--radius-lg);
    padding: 1.5rem 1rem;
    box-shadow: var(--sh1);
    transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--sh2);
}
.stat-num {
    font-family: var(--ff-display);
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--color-accent);
    line-height: 1;
    margin-bottom: 0.4rem;
}
.stat-label {
    font-size: 0.82rem;
    color: var(--color-text);
    line-height: 1.3;
    font-weight: 600;
}
.stat-label span[lang="en"] {
    display: block;
    font-size: 0.7rem;
    color: var(--color-text-muted);
    font-weight: 400;
    margin-top: 0.2rem;
}
@media (max-width: 640px) {
    .brand-hero { padding: 3rem 1rem 2rem; gap: 2.5rem; }
    .brand-hero-buttons { flex-direction: column; width: 100%; max-width: 280px; }
    .btn-primary, .btn-secondary { width: 100%; }
}
```

### 2.3 Feature 섹션 vanilla 번역

**원본 React 구조**: Feature1 = 좌측 텍스트(h4 + p + Button) + 우측 이미지

**번역 결정사항**:
- "A really compelling headline" → 행정 서비스 컨텍스트로 교체
- "Call to action" → 실제 액션으로 교체
- 우측 이미지는 **사용하지 않음**(placeholder 이미지). 대체로 **3단계 사용 흐름 일러스트** 또는 **체크리스트 카드**

**컨텐츠 후보 3개 중 1번을 기본으로 사용** (Claude Code가 판단 시 1번):

1. **"법령 기반 신뢰" 메시징**:
   - h4: "법무부 출입국·외국인정책본부 매뉴얼 기반"
   - 영문: "Built on Ministry of Justice Immigration Manual"
   - 본문: "본 서비스는 2026년 현행 출입국관리법 시행규칙과 출입국·외국인정책본부 실무 매뉴얼을 기반으로 합니다. 다만 최종 판단은 관할 출입국·외국인관서에 귀속됩니다."
   - 버튼: "1345 외국인종합안내센터" / "Contact 1345"

**HTML 구조**:
```html
<section id="brandFeature" class="brand-feature" aria-labelledby="brandFeatureTitle">
    <div class="feature-content">
        <h2 id="brandFeatureTitle" class="feature-headline">
            법무부 출입국·외국인정책본부<br>
            매뉴얼 기반
        </h2>
        <p class="feature-subtitle" lang="en">
            Built on Ministry of Justice Immigration Manual
        </p>
        <p class="feature-body">
            본 서비스는 2026년 현행 출입국관리법 시행규칙과 출입국·외국인정책본부
            실무 매뉴얼을 기반으로 합니다. 다만 최종 판단은 관할 출입국·외국인관서에
            귀속됩니다.
        </p>
        <a href="tel:1345" class="btn-primary feature-cta">
            <span>1345 외국인종합안내센터</span>
            <span class="btn-en" lang="en">Contact 1345</span>
        </a>
    </div>
    <aside class="feature-checklist" aria-label="서비스 핵심 기능">
        <ul class="check-list">
            <li><span class="check-icon" aria-hidden="true">✓</span>
                <div><strong>39개 체류자격 통합 검색</strong>
                <span lang="en">Search across 39 visa types</span></div></li>
            <li><span class="check-icon" aria-hidden="true">✓</span>
                <div><strong>자격별 구비서류 자동 생성</strong>
                <span lang="en">Auto-generated document checklist</span></div></li>
            <li><span class="check-icon" aria-hidden="true">✓</span>
                <div><strong>관할 출입국관서 즉시 조회</strong>
                <span lang="en">Find your jurisdiction office</span></div></li>
            <li><span class="check-icon" aria-hidden="true">✓</span>
                <div><strong>취업신고 직종·업종 코드</strong>
                <span lang="en">Employment notification codes</span></div></li>
        </ul>
    </aside>
</section>
```

**CSS**:
```css
.brand-feature {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
    padding: 4rem 2rem 6rem;
    max-width: 1160px;
    margin: 0 auto;
}
.feature-content {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}
.feature-headline {
    font-family: var(--ff-display);
    font-size: clamp(1.6rem, 3vw, 2.4rem);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: var(--color-primary-ink);
    margin: 0;
}
.feature-subtitle {
    font-size: 0.85rem;
    color: var(--color-text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin: 0;
}
.feature-body {
    font-size: 1rem;
    line-height: 1.65;
    color: var(--color-text);
    margin: 0;
    word-break: keep-all;
}
.feature-cta {
    align-self: flex-start;
    margin-top: 0.5rem;
}
.feature-checklist {
    background: var(--bg1);
    border: 1px solid var(--bd);
    border-radius: var(--radius-lg);
    padding: 1.8rem;
    box-shadow: var(--sh1);
}
.check-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
.check-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
}
.check-list li > div {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}
.check-list li strong {
    font-size: 0.95rem;
    color: var(--color-text);
    font-weight: 700;
}
.check-list li span[lang="en"] {
    font-size: 0.78rem;
    color: var(--color-text-muted);
}
.check-icon {
    flex-shrink: 0;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    background: var(--color-primary);
    color: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.85rem;
}
@media (max-width: 768px) {
    .brand-feature {
        grid-template-columns: 1fr;
        gap: 2rem;
        padding: 2rem 1rem 4rem;
    }
    .feature-cta { align-self: stretch; text-align: center; justify-content: center; }
}
```

### 2.4 다크모드 대응

브랜드 섹션이 다크모드에서도 작동하도록 검증:
- `var(--bg1)`, `var(--bd)`, `var(--color-text)` 등 기존 변수만 사용했다면 자동 대응됨
- 단, `.btn-primary`의 `color: #fff`는 다크모드에서도 흰색이 적절한지 확인 필요. `--color-primary` 위에 흰 텍스트는 명도 대비 충족(추정 — 별도 측정 권장).

---

## 3. Phase 3 — 검증 체크리스트

작업 완료 후 Claude Code가 스스로 확인할 항목. 미충족 항목이 있으면 수정 후 재검증.

```
□ index__22_.html 단일 파일 유지 (외부 의존성 추가 0)
□ React/JSX 구문 0개 (className, useState, import 등 없음)
□ Tailwind 클래스 0개 (text-[18px], bg-white, rounded-[12px] 등 없음)
□ <h1> 정확히 1개 (.logo-brand)
□ <main> 정확히 1개 (#mainContent)
□ <form role="search"> 검색 영역에 1개
□ 5개 모달 모두 role="dialog" aria-modal="true" aria-labelledby="..." 보유
□ 모든 input/textarea/select가 <label> 또는 aria-label 보유
□ alert() 호출 0개
□ onclick="..." 인라인 속성 0개 (data-action 패턴으로 통일)
□ "About us", "Call to action", "A really compelling headline" 영문 placeholder 0개
□ Device frame mockup 이미지 0개
□ 일출 캔버스 #starCanvas 정상 작동 유지
□ 39개 비자 검색 기능 정상 작동 유지
□ 키보드만으로 검색 → 결과 → 모달 진입 → ESC 닫기 가능
□ 모바일 360px 폭에서 brand-hero가 단일 컬럼으로 정상 표시
□ body.searched 상태에서 brand-hero, brand-feature가 숨겨짐
□ Lighthouse Accessibility 점수 90+ (개발자 도구로 측정)
```

---

## 4. 작업 순서 권장

1. **백업**: 현재 `index__22_.html`을 `index_backup.html`로 복사
2. **Phase 1.1 → 1.2 → 1.3 → 1.4** 순서로 접근성 작업 (시맨틱 마크업 먼저, 그 위에 ARIA)
3. **Phase 1.5 → 1.6 → 1.7** 모바일 + 인라인 정리
4. **Phase 2.1 → 2.2 → 2.3 → 2.4** Figma 섹션 추가
5. **Phase 3 검증**
6. **Git commit**: 각 Phase별로 커밋 분리. 메시지 규칙:
   - `feat(a11y): ...` (Phase 1)
   - `feat(brand): add hero/feature sections from Figma [figma-sync]` (Phase 2)
   - `chore(refactor): ...` (정리 작업)

---

## 5. 막혔을 때

- `VISA_DATA` 카테고리 분류 기준이 불분명 → 임시값(14/8/7/10) 유지 + TODO 주석
- 기존 JS 함수가 `data-action` 패턴과 충돌 → 기존 함수 시그니처 유지하고 위임 핸들러에서 호출만
- 다크모드에서 새 섹션이 깨짐 → `[data-theme="dark"]` 셀렉터로 변형 추가
- `:focus-visible`이 일부 브라우저(구형 Safari)에서 미지원 → polyfill 없이 `:focus`에 fallback 두기

---

> **최종 원칙**: "더 있어보이게"가 목표가 아니다. **외국인이 비자 정보를 찾으러 와서 신뢰감을 느끼고 헤매지 않게** 만드는 게 목표다. 한국 행정 서비스의 신뢰감은 SaaS 그라디언트가 아니라 **시맨틱·접근성·정확한 정보 구조**에서 나온다.