# Paradiso — Style Softening Brief
**레퍼런스: jackiezhang.co.za | 대상: Figma / Landing.tsx / paradiso.html**
*"딱딱함을 제거하되, 구조는 한 줄도 건드리지 않는다."*

---

## ⚠️ 브리프 읽기 전 주의

Jackie 본인이 Codrops 글에서 경고했다:
> *"The mistake was that I was translating a style instead of a concept."*

jackiezhang.co.za의 **스타일**은 손그림+종이질감+스크랩북이다.
그것을 Paradiso에 직역하면 공공서비스 비자 플랫폼이 아니라 낙서장이 된다.

번역해야 할 것은 스타일이 아니라 **컨셉이다:**
- 느껴지되 보이지 않는 질감 (texture that's **felt**, not seen)
- 자발적이고 따뜻한 느낌 (spontaneous, not precious)
- 경직된 디지털 그리드에서 유기적 리듬으로

이 브리프는 그 번역을 Paradiso 맥락(신뢰 + 공식성 + 한국어 UI)에 맞게 수행한다.

---

## Part 1 — Jackie Zhang 스타일 DNA (Paradiso 번역 기준)

| Jackie 원본 | Paradiso 번역 |
|---|---|
| 손그림 doodle 요소 | → CSS 기반 유기적 클립 패스 (torn edge), SVG 언더라인 accent |
| 종이 질감 grain overlay | → 매우 미묘한 노이즈 SVG 필터 (opacity 0.025–0.04) |
| top-border highlight (inner shadow 대신) | → `box-shadow: inset 0 1px 0 rgba(255,255,255,0.6)` |
| Serif + Handwritten 폰트 쌍 | → Noto Serif KR (display) + Noto Sans KR (body) weight 대비 강화 |
| Primary + BW only 색상 | → 그린(#0EA37B) 시그니처 단독 강조, 나머지 중성화 |
| 고정 크기, bounded layout | → 섹션별 max-width 변화로 템포 만들기 |
| 드래그 가능한 tactile 인터랙션 | → hover에 미세한 scale + rotate 조합 (CSS only) |
| 오버사이즈 display 타이포 | → hero h1을 clamp 상한 높이기 (max 5.5rem→7rem) |

---

## Part 2 — 현재 Paradiso의 딱딱함 진단

### 2-1. 타이포그래피 위계 붕괴

**문제:** 거의 모든 텍스트가 `font-weight: 900 (extrabold)`다.
h1, h2, h3, h4, stat 숫자, checklist ko 텍스트, brand-h2 — 전부 900.
무게 대비가 없으면 시각 피라미드가 사라진다.

**현재 스택 (사실):**
```
hero h1        → 900, clamp(2.5rem, 6vw, 4.5rem)
brand h2       → 900, clamp(2rem, 4.5vw, 3.5rem)
feature h2     → 900, clamp(1.75rem, 3vw, 3rem)
checklist .ko  → 900, 1.05rem
stat num       → 900, 3rem
stat label     → 900, .9rem     ← 이건 말이 안 됨
```

**Jackie 방식:** display(serif heavy) ↔ body(sans light) 대비로 위계 만듦

### 2-2. Border-radius 단조로움

**문제:** 전체 사이트에 32px 반경이 반복된다.
feature card, anagram section, start-img, value card, footer-hero — 모두 `border-radius: 2rem`.
같은 반경이 모든 컨테이너에 적용되면 단일한 코퍼레이트 UI처럼 보인다.

**Jackie 방식:** 크기와 목적에 따라 반경 변주. 작은 요소는 더 둥글게, 큰 컨테이너는 덜 둥글게.

### 2-3. 그림자 층위 없음

**문제:** 두 가지 그림자만 존재한다: `0 20px 60px rgba(0,0,0,.15)` (large) 와 `0 2px 8px rgba(0,0,0,.05)` (small).
중간 층위가 없어 z-depth 감각이 없다.

### 2-4. 섹션 간 색상 온도 변화 없음

**문제:** 히어로(검정+이미지) → 브랜드(파란 그라디언트) → 피처(흰색) → About(오프화이트) → 푸터(흰색)
색상 온도가 불규칙하게 점프하며, 특히 브랜드 섹션의 `#5b7ea6→#7aaa8a→#2d6a8f` 그라디언트는
전체 색상 시스템(그린/코럴/샌드)과 겉돌아 따로 논다.

### 2-5. 여백 리듬 단조로움

**문제:** `6rem`, `8rem` 간격이 전체 반복. 섹션마다 같은 무게감.
Jackie는 "Keep it bounded" 원칙으로 각 섹션에 다른 내부 밀도를 줬다.

---

## Part 3 — CSS 수정 방안 (섹션별)

> **규칙:**
> - HTML 구조 변경 없음
> - 기존 선택자에 속성 추가/수정만
> - React 컴포넌트 사용 중이면 className 수정, CSS 변수 수정 허용
> - 새 외부 의존성 없음 (Google Fonts는 이미 로드 중)

---

### 3-1. 타이포그래피 시스템 재조정

**목표:** display (무거운 세리프) ↔ body/label (가벼운 sans) 대비 생성

```css
/* ─── 폰트 로드 추가 ─────────────────────────── */
/* 기존 Google Fonts URL에 아래 추가 */
/* Noto Serif KR:wght@300;400;700 + Noto Sans KR:wght@300;400;500;700 */
/* (이미 Noto Sans KR 로드 중이면 weight 300, 500 추가만) */

/* ─── 루트 변수 추가 ────────────────────────── */
:root {
  --font-display: 'Noto Serif KR', serif;
  --font-body:    'Noto Sans KR', sans-serif;

  /* 현재: 전부 900. 아래로 교체 */
  --weight-display: 700;   /* 세리프 헤드라인 */
  --weight-strong:  800;   /* 강조 숫자/중요 레이블 */
  --weight-body:    400;   /* 본문 */
  --weight-label:   500;   /* 소문자 레이블 */
  --weight-meta:    300;   /* 날짜, 영문 서브텍스트 */
}

/* ─── 섹션별 적용 ───────────────────────────── */

/* Hero h1: 세리프 + 덜 무거운 무게로 elegance */
.hero-title {
  font-family: var(--font-display);
  font-weight: 700;          /* 900 → 700 */
  letter-spacing: -0.04em;   /* 더 타이트하게, 세리프 특성 살림 */
  line-height: 1.1;
}

/* Brand h2: 세리프 유지, 무게 약화로 서정성 */
.brand-h2 {
  font-family: var(--font-display);
  font-weight: 700;           /* 900 → 700 */
  letter-spacing: -0.035em;
}

/* Stat 숫자: 코럴 컬러 + 무게는 강조 */
.stat-num {
  font-weight: 800;           /* 900 → 800, 눈에 띄되 덜 날카롭게 */
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.05em;
}

/* Stat label: 현재 900 → 불필요하게 무거움 */
.stat-label {
  font-weight: 600;           /* 900 → 600 */
}
.stat-en {
  font-weight: 400;           /* 700 → 400 */
  letter-spacing: 0.08em;
}

/* Feature h2 */
.feature-h2 {
  font-family: var(--font-display);
  font-weight: 700;           /* 900 → 700 */
}

/* Feature 본문 */
.feature-desc {
  font-weight: 400;           /* 500 → 400 */
  line-height: 1.85;          /* 행간 넓게 */
  color: #555;                /* #4b5563 보다 조금 더 밝게 */
}

/* Check 한글 */
.check-ko {
  font-weight: 700;           /* 900 → 700 */
}

/* Value card 제목 */
.value-card h4 {
  font-family: var(--font-display);
  font-weight: 700;           /* 900 → 700 */
}

/* Roadmap 제목 */
.roadmap-row h4 {
  font-weight: 700;           /* 900 → 700 */
}

/* About section 대제목 */
.about-title {
  font-family: var(--font-display);
  font-weight: 700;           /* 900 → 700 */
}

/* Footer hero h2 */
.footer-hero h2 {
  font-family: var(--font-display);
  font-weight: 700;           /* 900 → 700 */
  letter-spacing: -0.04em;
}
```

**효과:** 같은 Noto 패밀리 내에서도 세리프/700 vs 산스/400의 대비가 만들어지면
시각 위계가 생기고 부드러운 느낌이 온다. Jackie의 "serif as grid lines, doodle on top" 번역.

---

### 3-2. 그림자 시스템 재조정 (3-tier)

```css
/* ─── 현재: 두 단계만 존재 ───────────────────── */
/* 수정: 3단계 레이어로 물리적 깊이감 */

:root {
  /* Tier 1 — 부유하는 느낌 (stat card, feature card) */
  --shadow-float:
    0 2px 4px rgba(0,0,0,.04),
    0 8px 20px rgba(0,0,0,.06),
    0 20px 40px rgba(0,0,0,.06);

  /* Tier 2 — 올라오는 느낌 (value cards, checklist items) */
  --shadow-lift:
    0 1px 3px rgba(0,0,0,.06),
    0 4px 12px rgba(0,0,0,.08);

  /* Tier 3 — 바닥에 붙은 느낌 (stat tags, badges) */
  --shadow-press:
    0 1px 2px rgba(0,0,0,.06);

  /* Jackie 방식: top-border highlight */
  --highlight-top: inset 0 1px 0 rgba(255,255,255,0.65);
}

/* 적용 */
.stat-grid {
  box-shadow: var(--shadow-float);
}

.feature-card {
  box-shadow: var(--shadow-float), var(--highlight-top);
  /* 기존 0 4px 40px rgba(0,0,0,.06) → 더 자연스러운 3단계로 교체 */
}

.checklist li {
  box-shadow: var(--shadow-press), var(--highlight-top);
}

.value-card {
  box-shadow: var(--shadow-lift);
  /* hover 시에만 float로 올라옴 */
}

.value-card:hover {
  box-shadow: var(--shadow-float);
}

.anagram-visual {
  box-shadow: var(--shadow-lift), var(--highlight-top),
              inset 0 2px 12px rgba(0,0,0,.04);
}
```

---

### 3-3. Border-radius 차별화

```css
/* 현재: 전체 2rem(32px) 동일 → 기계적 */
/* 수정: 컨테이너 크기에 반비례 적용 */

/* 큰 컨테이너 → 덜 둥글게 (더 건축적) */
.feature-card    { border-radius: 1.5rem; }  /* 32 → 24px */
.anagram-section { border-radius: 1.5rem; }  /* 32 → 24px */
.footer-hero     { border-radius: 2rem; }    /* 2.5rem → 2rem */

/* 중간 컨테이너 → 유지 */
.anagram-visual  { border-radius: 1.25rem; } /* 1.5rem → 1.25rem (20px) */

/* 작은 요소 → 더 둥글게 (playful) */
.checklist li    { border-radius: 1rem; }    /* 유지 */
.stat-tag        { border-radius: 9999px; }  /* 유지 (pill) */
.check-icon      { border-radius: 50%; }     /* 유지 */

/* Value card: 오히려 더 둥글게 — 카드 느낌 강화 */
.value-card      { border-radius: 2.5rem; }  /* 2rem → 2.5rem */

/* Start image: 살짝 기울기와 더 큰 반경으로 사진 느낌 */
.start-img       {
  border-radius: 1.75rem;
  /* 기울기는 hover에만 */
}
.start-img:hover {
  transform: rotate(-0.5deg) scale(1.01);
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

### 3-4. 브랜드 섹션 그라디언트 교체

```css
/* 현재: #5b7ea6→#7aaa8a→#2d6a8f (파란-녹색 혼합) */
/* 문제: 전체 그린/코럴 팔레트와 따로 놈 */
/* 수정: Paradiso 색상 시스템 내로 끌어오기 */

#brand {
  background:
    linear-gradient(
      160deg,
      #085E48 0%,           /* 딥 그린 */
      #0EA37B 45%,          /* 시그니처 그린 */
      #085E48 100%          /* 딥 그린으로 귀환 */
    );
  /* 기존 파랑 계열 완전 제거 */
}

/* 배경 이미지 overlay 조정 */
#brand-bg img {
  opacity: 0.12;             /* 0.2 → 0.12 */
  mix-blend-mode: luminosity; /* overlay → luminosity: 더 부드럽게 */
}

/* Brand h2 아래 서브텍스트 */
.brand-sub {
  font-weight: 400;          /* 700 → 400 (현재 너무 강함) */
  letter-spacing: 0.15em;
  opacity: 0.75;             /* 흰색 바탕에 살짝 뒤로 */
}
```

---

### 3-5. 노이즈 질감 오버레이 (Jackie DNA의 핵심)

Jackie는 "texture that's felt, not seen"을 SVG 필터로 구현했다.
Paradiso에 적용하면 공공서비스의 권위감을 유지하면서 따뜻함을 추가할 수 있다.

```css
/* ─── SVG 노이즈 필터 정의 ─────────────────── */
/* <body> 직후 또는 <head> 안에 추가 */
/*
<svg style="position:absolute;width:0;height:0;">
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3"
                  stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
    <feBlend in="SourceGraphic" mode="multiply"/>
  </filter>
</svg>
*/

/* ─── CSS 적용 ──────────────────────────────── */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  opacity: 0.028;            /* 거의 안 보이는 수준 */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px 200px;
}

/* ─── 특정 섹션에만 적용하고 싶다면 ─────────── */
#feature .feature-card::before {
  content: '';
  position: absolute; inset: 0;
  border-radius: inherit;
  background-image: url("data:image/svg+xml,..."); /* 동일 */
  opacity: 0.02;
  pointer-events: none;
  z-index: 1;
}
```

**주의:** opacity를 0.03 이상으로 올리면 Jackie가 말한 "dirty texture" 영역에 진입. 0.02–0.03 유지.

---

### 3-6. 전환 효과 (Transitions) 부드럽게

```css
/* 현재: .2s linear / .3s 등 직선적 */
/* 수정: spring-like easing으로 tactile 느낌 */

:root {
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);  /* overshoot */
  --ease-out-soft: cubic-bezier(0.16, 1, 0.3, 1);    /* 부드러운 감속 */
  --ease-in-out-smooth: cubic-bezier(0.45, 0, 0.55, 1);
}

/* 버튼 hover */
.btn-white,
.btn-outline,
.btn-dark,
.btn-search,
.btn-login {
  transition:
    transform 0.25s var(--ease-spring),
    box-shadow 0.25s var(--ease-out-soft),
    background-color 0.2s ease,
    border-color 0.2s ease;
}

.btn-white:hover,
.btn-dark:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-float);
}

/* Quick 버튼 */
.quick-btn {
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    transform 0.3s var(--ease-spring);
}

.quick-btn:hover {
  transform: translateY(-3px) scale(1.02);
}

/* Value cards */
.value-card {
  transition:
    transform 0.4s var(--ease-spring),
    box-shadow 0.4s var(--ease-out-soft);
}

/* Checklist items */
.checklist li {
  transition: transform 0.25s var(--ease-spring);
}

/* Roadmap dot */
.roadmap-dot {
  transition: transform 0.3s var(--ease-spring);
}
```

---

### 3-7. Organic Edge Accent (Jackie의 torn paper 번역)

Jackie는 실제 찢어진 종이 모양 SVG 클립을 사용했다.
Paradiso에서는 브랜드 섹션 하단에 부드러운 웨이브로 번역한다.

```css
/* BrandHero 하단에 웨이브 accent */
#brand::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0; right: 0;
  height: 80px;
  background: var(--sand);       /* #fcfaf5 — 다음 섹션 배경색 */
  clip-path: ellipse(55% 100% at 50% 100%);
  /* 또는 더 유기적으로: */
  /* clip-path: polygon(0 60%, 8% 40%, 20% 55%, 35% 30%, 50% 50%, 65% 25%, 80% 45%, 92% 35%, 100% 55%, 100% 100%, 0 100%); */
}

/* stat-grid는 이 after 위에 올라오므로 z-index 확인 */
.stat-grid {
  z-index: 20; /* 기존 유지 */
}
```

---

### 3-8. 색상 팔레트 집중화

Jackie: "Primary + Black/White ONLY — constraint is direction"
Paradiso 번역: 그린을 메인 시그니처로, 코럴은 숫자 강조에만 집중

```css
:root {
  /* ─── 유지 ────────────────── */
  --green:       #0EA37B;
  --green-dark:  #085E48;
  --coral:       #FF6B5B;
  --sand:        #fcfaf5;
  --border-warm: #D8CAB0;

  /* ─── 신규 추가 (중성화) ───── */
  --neutral-900: #111111;
  --neutral-700: #374151;
  --neutral-500: #6b7280;
  --neutral-300: #d1d5db;
  --neutral-100: #f9fafb;

  /* ─── 줄이기 ───────────────── */
  /* --coral-light: #FFB8A8  → 사용 빈도 최소화 (stat tags 제거, accent만) */
  /* --teal-light:  #7DD8B8  → footer hero eyebrow에만 유지 */
  /* #5b7ea6, #7aaa8a, #2d6a8f → 브랜드 섹션에서 제거 (3-4에서 교체됨) */
}

/* 코럴을 숫자 강조로만 제한 */
/* stat-num: coral 유지 */
/* coral-light(#FFB8A8): anagram section 그라디언트에만 */
/* 나머지 coral 사용처는 green으로 교체 가능 여부 검토 */

/* roadmap-dot: coral → green-dark로 교체 고려 */
.roadmap-dot {
  background: var(--green);        /* #FF6B5B → #0EA37B */
  box-shadow: 0 0 0 4px rgba(14,163,123,0.2); /* coral ring → green ring */
}
```

---

### 3-9. 히어로 타이포그래피 임팩트 강화

```css
/* 현재: clamp(2.5rem, 6vw, 4.5rem) */
/* 수정: 상한 높여서 대형 화면에서 oversized 임팩트 */

.hero-title {
  font-size: clamp(2.75rem, 7vw, 6rem);  /* max 4.5rem → 6rem */
  font-family: var(--font-display);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.04em;
  /* 현재 mb-12 유지 */
}

/* 히어로 서브카피 (없다면 추가 고려) */
/* 현재 h1 직후 바로 검색창 → 중간에 한 줄 서브카피 공간 */
/* <p class="hero-sub">출입국·외국인정책본부 실무 매뉴얼 기반 • 2026 현행</p> */
.hero-sub {
  font-size: 0.875rem;
  font-weight: 400;
  color: rgba(255,255,255,0.55);
  letter-spacing: 0.05em;
  margin-bottom: 2rem;    /* 검색창 위 */
  margin-top: -2rem;      /* h1과 가깝게 */
}
```

---

### 3-10. Scroll Reveal 애니메이션 부드럽게

```css
/* 현재: opacity 0→1, translateY 24px→0 */
/* 수정: 더 긴 duration + spring easing */

.reveal {
  opacity: 0;
  transform: translateY(32px);           /* 24 → 32px */
  transition:
    opacity  0.9s var(--ease-out-soft),
    transform 0.9s var(--ease-out-soft);
}

.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}

/* 지연 유틸리티 — HTML에 style="--delay:0.1s" 형태로 */
.reveal {
  transition-delay: var(--delay, 0s);
}
```

---

## Part 4 — 콘텐츠 구체화 가이드

> **GitHub Moonshot 리포지토리 URL 미제공** → 현재 Landing.tsx 텍스트 기준으로 제안.
> 리포지토리 URL 제공 시 이 섹션 업데이트 필요.

### 현재 텍스트 vs 제안 텍스트

#### Hero

| 위치 | 현재 | 제안 |
|---|---|---|
| h1 | 대한민국 39가지<br>체류자격을 한 번에 | **대한민국 39가지**<br>**체류자격,** 한 번에. |
| 검색 placeholder | 비자 코드 및 키워드 직접 검색 (예: 유학, 취업, F-2) | 비자 코드·자격명·상황어로 검색 (예: E-7, 결혼, 유학생) |

> **의도:** 마침표(.) 추가 → 확언적이고 덜 나열적. "상황어로 검색"은 AI 기능 암시.

#### Brand Hero

| 위치 | 현재 | 제안 |
|---|---|---|
| h2 | 분절된 체류 행정,<br>단일 플랫폼으로 통합하다. | **흩어진 체류 정보를**<br>**한 곳으로.** |
| sub | Korea's 39 visa categories. Unified. | Korea's 39 visa types — searched, sorted, simplified. |

> **의도:** "분절" "통합" 등 행정 용어 → "흩어진" "한 곳으로" 더 인간적.

#### Feature Section

| 위치 | 현재 | 제안 |
|---|---|---|
| h2 | 법무부 출입국·외국인정책본부<br>매뉴얼 기반 | **법무부 공식 매뉴얼**을<br>그대로 담았습니다. |
| desc | 본 서비스는 2026년 현행 출입국관리법... | 출입국관리법 시행규칙(2026년 현행)과 출입국·외국인정책본부 실무 매뉴얼을 1차 출처로 합니다. 최종 판단은 관할 관서에 귀속됩니다. |

> **의도:** "기반"을 "그대로 담았습니다"로 → 서비스의 신뢰 근거를 더 적극적으로 서술.

#### Checklist (Feature 우측)

| 현재 | 제안 |
|---|---|
| 39개 체류자격 통합 검색 | 39개 자격 통합 검색 — 코드·이름·상황어 모두 |
| 자격별 구비서류 자동 생성 | 내 자격에 맞는 서류 목록 자동 생성 |
| 관할 출입국관서 즉시 조회 | 주소 입력 → 관할 관서 즉시 확인 |
| 취업신고 직종·업종 코드 | 취업신고용 직종·업종 코드 조회 |

> **의도:** 기능 설명 → 사용자 입장의 행동/결과 언어로 전환.

#### Stat Cards

| 현재 | 제안 |
|---|---|
| 14 / 취업·전문직 | **14개** / 취업·전문직 자격 |
| 8 / 유학·연수 | **8개** / 유학·연수 자격 |
| 7 / 거주·결혼 | **7개** / 거주·결혼 자격 |
| 10 / 방문·기타 | **10개** / 방문·기타 자격 |

> **의도:** 숫자 뒤 "개" 추가 → 한국어 맥락 자연스러움.

#### About — Paradiso의 시작

| 현재 | 제안 |
|---|---|
| (긴 단락) | **300만 체류 외국인 시대.** 39가지 자격은 있지만 정보는 흩어져 있습니다. Paradiso는 출입국·외국인정책본부 실무 매뉴얼을 기반으로, 가장 정확한 비자 정보를 단일 플랫폼에서 제공합니다. |

> **의도:** 숫자(300만)를 앞으로 끌어내 임팩트 강화. 단락 길이 절반으로 축소.

#### Roadmap

| 현재 | 제안 |
|---|---|
| 2026 Q3 — 정식 서비스 런칭 | **2026 Q3** — 정식 런칭 + 영어·중국어·베트남어 UI |
| 2026 Q1 — AI 맞춤형 비자 진단 | **2026 Q1** — AI 비자 진단 (RAG 기반 매뉴얼 검색) |
| 2025 Q4 — 공공데이터 공모전 | **2025 Q4** — MVP 공개 (공공데이터 활용 공모전 출품) ✓ |

> **의도:** 2025 Q4는 이미 완료 → ✓ 마크로 진행 상황 명시.

---

## Part 5 — 수정 적용 순서 (우선순위)

### Wave A — 즉시, 15분 (임팩트/리스크 = 최고/최저)
1. `--ease-spring`, `--ease-out-soft` CSS 변수 추가
2. 버튼 transition 교체 (3-6)
3. `#brand` 그라디언트 교체 → 그린 계열로 (3-4)
4. `.roadmap-dot` 색상 → 그린으로 (3-8)

### Wave B — 30분 (타이포그래피 시스템)
5. `font-family: var(--font-display)` 헤드라인 적용 (3-1)
6. 주요 `font-weight` 900 → 700 교체 (3-1)
7. 그림자 변수 추가 + 적용 (3-2)

### Wave C — 1시간 (공간 + 질감)
8. `border-radius` 차별화 (3-3)
9. 노이즈 텍스처 오버레이 (3-5) — opacity 조심
10. `#brand::after` 웨이브 accent (3-7)
11. 히어로 타이포 임팩트 강화 (3-9)
12. scroll reveal easing 교체 (3-10)

### Wave D — 콘텐츠 (별도 작업)
13. GitHub Moonshot 리포지토리 확인 후 텍스트 구체화 (Part 4)

---

## Part 6 — 절대 바꾸지 말아야 할 것

| 항목 | 이유 |
|---|---|
| 색상 변수 `--green`, `--coral`, `--sand` | 브랜드 아이덴티티 |
| 로고 SVG | Paradiso 시각 정체성 핵심 |
| `stat-num` 코럴 색상 | 숫자 강조의 유일한 accent |
| 애너그램 JS 로직 | 이번 스코프 밖 |
| 검색/결과/모달 기능 | 기능 로직 무관 |
| `#brand-bg img` mix-blend-mode | 이미 올바름 |
| `footer-hero-eyebrow` `#7DD8B8` | 클로징 섹션 포인트 색상 |
| Phase 9A에서 이미 확정된 수정 내용 | 중복 변경 금지 |

---

## 부록 — "느껴지되 보이지 않는 질감" 체크리스트

적용 후 아래를 순서대로 확인하라:

- [ ] 히어로 h1이 세리프로 바뀌었는가 → 그린 검색 버튼과 대비가 명확한가
- [ ] 브랜드 섹션 배경이 그린 계열인가 → 전체 색상 시스템과 통일되었는가
- [ ] stat card 그림자가 공중에 뜬 느낌인가
- [ ] 버튼 hover 시 spring bounce가 느껴지는가 (0.5초 안에)
- [ ] value card hover 시 살짝 올라오는 느낌인가
- [ ] 노이즈 텍스처가 **보이지 않는가** (보이면 opacity 낮추기)
- [ ] 전체 스크롤 시 각 섹션이 다른 무게감으로 느껴지는가
- [ ] 폰트 weight 900이 h1/h2에만 남아있고 body는 400인가

모든 체크가 완료되면 딱딱함이 제거된 것이다.
