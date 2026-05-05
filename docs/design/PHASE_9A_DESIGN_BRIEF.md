# Paradiso — Phase 9A Design Correction Brief
**Senior Product Design Review**
*Figma Reference: Landing.tsx (React/Tailwind source) vs. Production: paradiso.html (Vanilla HTML/CSS)*
*Date: 2026-05-06 | Reviewer: AI Design Reviewer*

---

## 분석 방법론

1. Figma 원본 `Landing.tsx`의 Tailwind 클래스를 픽셀 환산하여 기준값 도출
2. 복원된 `paradiso.html`(production reference)의 실제 CSS 블록을 selector별로 추출
3. 두 값의 delta를 시각적 임팩트 기준으로 우선순위화
4. CSS-only 수정 가능 여부 판별 (JS 변경 없이)

---

## A. Top 10 최고 임팩트 시각적 갭

---

### GAP #1 — Stat Card 수직 오버랩 (translateY)
**섹션 리듬 붕괴 — 가장 높은 임팩트**

| | Figma 원본 | Production 현재 |
|---|---|---|
| Stat grid 수직 이동 | `md:translate-y-1/2` ≈ 카드 높이의 50% (~200–250px) | `transform: translateY(3.5rem)` = 고정 **56px** |
| 효과 | BrandHero 하단을 침범하며 FeatureSection과 시각적 브리지 형성 | 미세하게 내려와 오버랩 효과 사실상 없음 |
| Feature section 상단 패딩 | `pt-16 md:pt-48` = mobile 64px / desktop **192px** (stat card 높이 확보) | `padding-top: 11rem` = **176px** (근사치지만 stat card가 56px만 내려오므로 공간 과잉) |

**증상:** BrandHero → FeatureSection 전환이 밋밋함. 섹션 경계가 단절되어 스크롤 리듬이 죽음.

---

### GAP #2 — Hero 이미지 그라디언트 혼합 모드 누락
**분위기 전체가 달라지는 갭**

| | Figma 원본 | Production 현재 |
|---|---|---|
| 오버레이 레이어 | `bg-gradient-to-t from-black via-black/40 to-black/60` + **`mix-blend-multiply`** | 그라디언트는 있음, `mix-blend-multiply` **없음** |
| 이미지 opacity | `opacity-80` (클래스) | `opacity: .8` (동일) |

**증상:** 낮 풍경 사진일 때 히어로가 너무 밝음. `mix-blend-multiply`가 없으면 그라디언트 검정이 사진 위에 단순 '덮기'가 되어 영화적 분위기가 사라짐.

---

### GAP #3 — Feature Card 내부 패딩 반응형 차이
**카드 숨쉬기 공간 부족**

| | Figma 원본 | Production 현재 |
|---|---|---|
| Feature card padding | `p-8 md:p-16` = mobile **32px** / desktop **64px** | `padding: 4rem` = **64px flat** (모바일도 64px) |
| Gap (좌우 컬럼) | `gap-12 md:gap-20` = mobile 48px / desktop **80px** | `gap: 5rem` = **80px flat** |

**증상:** 모바일에서 feature card가 과도하게 넓게 펼쳐져 답답함. 반응형 패딩 의도가 실현되지 않음.

---

### GAP #4 — About 섹션 수직 리듬 (공간 스케일)
**스크롤 페이싱 평탄화**

| | Figma 원본 | Production 현재 |
|---|---|---|
| 서브섹션 간 spacing | `space-y-24 md:space-y-32` = mobile **96px** / desktop **128px** | 각 요소 `margin-bottom: 6rem` = **96px flat** |
| 모바일 영향 | 96px (적정) | 96px (동일 → 모바일에서 너무 늘어짐) |

**증상:** 모바일에서 About 섹션이 끝없이 스크롤됨. desktop의 `128px`은 여유롭지만 모바일 `96px`은 과도함.

---

### GAP #5 — Anagram 비주얼 패널 내부 처리
**브랜드 섹션의 보석 역할이 흐릿함**

| | Figma 원본 | Production 현재 |
|---|---|---|
| 외부 패널 | `bg-white/60 backdrop-blur-md rounded-3xl p-8 py-16 shadow-inner border border-white/50` | `border-radius: 1.5rem; padding: 3rem 2rem;` — `shadow-inner`, `border-radius: 24px(rounded-3xl=1.5rem` OK), py-16(64px) **누락** |
| 내부 배경 | `box-shadow: inset 0 2px 12px rgba(0,0,0,.04)` | `shadow-inner` **없음** |
| 상하 패딩 | `py-16` = **64px** | `padding: 3rem 2rem` = **48px 32px** (상하 부족) |

**증상:** Anagram이 공중에 떠 있는 느낌 없이 평판에 붙어있음. 유리 패널 효과가 반감됨.

---

### GAP #6 — Nav 수평 패딩 (모바일)
**상단 좌우 여백 과잉**

| | Figma 원본 | Production 현재 |
|---|---|---|
| Nav padding | `px-6 md:px-12` = mobile **24px** / desktop **48px** | `padding: 2rem 3rem` = **32px 48px flat** |
| 결과 | 모바일에서 로고가 중앙에 자리잡음 | 모바일에서 좌우 여백 32px → 로고+버튼이 비좁게 보임 |

---

### GAP #7 — BrandHero 상하 패딩 + 이미지 믹스블렌드
**섹션 부피감 차이**

| | Figma 원본 | Production 현재 |
|---|---|---|
| BrandHero padding | `py-24 md:py-32` = mobile **96px** / desktop **128px** | `padding: 8rem 1.5rem` = **128px flat** |
| 배경 이미지 | `opacity-20 mix-blend-overlay` | `opacity:.2 mix-blend-overlay` — **동일** (이건 OK) |

**증상:** 모바일에서 BrandHero가 너무 길어 stat card가 멀리 떨어짐. desktop은 OK.

---

### GAP #8 — Footer Hero 높이 + 상단 마진
**랜딩의 클로징 펀치 약화**

| | Figma 원본 | Production 현재 |
|---|---|---|
| 높이 | `h-[480px] md:h-[500px]` | `height: 30rem` = **480px flat** (모바일도 480px) |
| 상단 마진 | `mt-32` = **128px** (About 서브섹션과의 명확한 분리) | 없음 (margin-top 미정의) |
| border-radius | `rounded-[40px]` = **40px** | `border-radius: 2.5rem` = **40px** ✓ |

**증상:** 모바일에서 footer hero가 불필요하게 크게 차지. 그리고 로드맵과의 간격 부족.

---

### GAP #9 — Value Cards (HobbyCard) 그림자 + hover
**카드 부피감 부족**

| | Figma 원본 | Production 현재 |
|---|---|---|
| Shadow | `shadow-lg` = `0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)` | `box-shadow: 0 8px 32px rgba(0,0,0,.1)` — 유사하나 레이어 없음 |
| hover translate | `hover:-translate-y-2` = **-8px** | `transform: translateY(-8px)` ✓ |
| 아이콘 박스 | `w-14 h-14 rounded-2xl` = 56px / 16px radius | `width: 3.5rem height: 3.5rem` = 56px, `border-radius: 1rem` = 16px ✓ |

---

### GAP #10 — Search Bar 형태 (pill vs rounded-2xl)
**히어로 핵심 인터랙션 요소의 형태 불일치**

| | Figma 원본 | Production 현재 |
|---|---|---|
| Search bar shape | `rounded-2xl md:rounded-full` = mobile **16px** / desktop **pill** | `border-radius: 1.25rem` = **20px flat** |
| Search button | `rounded-xl md:rounded-full` = mobile **12px** / desktop **pill** | `border-radius: 1rem` = **16px flat** |
| Focus ring | `focus-within:bg-white/25 focus-within:border-white/50` | `background .2s, border-color .2s` transition 있음, focus-within 값은 유사 |

**증상:** desktop에서 검색바가 pill 형태(완전 원형)여야 하는데 각진 사각형으로 보임.

---

## B. CSS-only 수정안 (Selector별)

> **주의:** 아래는 production `paradiso.html`의 기존 선택자에 추가/수정할 CSS만 기술한다.  
> HTML 구조, JS, 기능 로직은 **일절 건드리지 않는다.**

---

### FIX #1 — Stat Card translateY 복원

```css
/* 기존: transform: translateY(3.5rem) */
/* 변경: desktop에서 카드 자체 높이의 절반만큼 아래로 내려보냄 */

.stat-grid {
  /* 기존 속성 유지하면서 이것만 변경 */
  transform: translateY(3.5rem); /* 모바일 유지 */
}

@media (min-width: 768px) {
  .stat-grid {
    transform: translateY(50%);
    /* stat-grid의 실제 렌더링 높이에 의존 — 대략 220-260px 예상 */
    /* 50% = 카드 컨테이너 높이의 절반 */
  }

  #feature {
    /* 기존 11rem에서 stat grid 오버랩 공간 확보 */
    padding-top: 12rem; /* stat card가 ~260px이므로 절반 130px + 여백 62px */
  }
}
```

**리스크:** MEDIUM — `translateY(50%)`는 `.stat-grid` 자체 높이 기준. 컨텐츠 양에 따라 달라질 수 있음. 실측 후 `clamp(7rem, calc(50% of actual height), 16rem)` 형태로 조정 필요할 수 있음. 대안: `translateY(calc(50cqh))` 또는 `translateY(min(50%, 14rem))`.

---

### FIX #2 — Hero Overlay mix-blend-multiply 추가

```css
/* 기존 #hero-overlay에 mix-blend-mode 추가 */

#hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, #000 0%, rgba(0,0,0,.4) 45%, rgba(0,0,0,.6) 100%);
  mix-blend-mode: multiply; /* 이것만 추가 */
}
```

**리스크:** LOW — 순수 CSS 한 줄 추가. 사진 색조에 따라 시각 효과 달라질 수 있으나, 어두운 방향이므로 가독성에 유리.

---

### FIX #3 — Feature Card 반응형 패딩

```css
/* 기존: padding: 4rem; gap: 5rem; */

.feature-card {
  padding: 2rem;  /* mobile */
  gap: 3rem;      /* mobile */
}

@media (min-width: 1024px) {
  .feature-card {
    padding: 4rem;  /* desktop */
    gap: 5rem;      /* desktop */
  }
}
```

**리스크:** LOW — 단순 반응형 패딩. 기존 desktop 값 그대로 보존.

---

### FIX #4 — About 섹션 모바일 spacing 축소

```css
/* 기존: 각 서브섹션 margin-bottom: 6rem flat */
/* 변경: 모바일에서 줄이기 */

.anagram-section,
.start-section,
.values-section,
.roadmap-section {
  margin-bottom: 4rem; /* mobile */
}

@media (min-width: 768px) {
  .anagram-section,
  .start-section,
  .values-section,
  .roadmap-section {
    margin-bottom: 6rem; /* desktop 유지 */
  }
}

/* About 섹션 자체 vertical padding */
#about {
  padding-top: 4rem;  /* mobile */
  padding-bottom: 4rem;
}

@media (min-width: 768px) {
  #about {
    padding-top: 6rem;
    padding-bottom: 6rem;
  }
}
```

**리스크:** LOW — 기존 desktop 값 보존, 모바일만 축소.

---

### FIX #5 — Anagram 패널 shadow-inner + 패딩

```css
/* 기존: .anagram-visual { padding: 3rem 2rem; } */

.anagram-visual {
  padding: 4rem 2rem;                          /* py-16(64px) 반영 */
  box-shadow: inset 0 2px 12px rgba(0,0,0,.04); /* shadow-inner 추가 */
  /* 나머지 속성 그대로 유지 */
}
```

**리스크:** LOW — 패딩 증가 + shadow-inner 추가. 레이아웃 밀리는지 확인 필요.

---

### FIX #6 — Nav 모바일 패딩 교정

```css
/* 기존: nav { padding: 2rem 3rem; } */

nav {
  padding: 1.5rem; /* mobile: 24px all sides */
}

@media (min-width: 768px) {
  nav {
    padding: 2rem 3rem; /* desktop: 기존 유지 */
  }
}
```

**리스크:** LOW — 모바일 여백 조정만.

---

### FIX #7 — BrandHero 모바일 패딩 축소

```css
/* 기존: #brand { padding: 8rem 1.5rem; } */

#brand {
  padding: 6rem 1.5rem; /* mobile: py-24 = 96px */
}

@media (min-width: 768px) {
  #brand {
    padding: 8rem 1.5rem; /* desktop: py-32 = 128px */
  }
}
```

**리스크:** LOW — stat card translateY와 연동되므로 FIX #1과 함께 적용.

---

### FIX #8 — Footer Hero 높이 반응형 + 상단 마진

```css
/* 기존: .footer-hero { height: 30rem; } */

.footer-hero {
  height: 26rem;    /* mobile: ~416px 적정 */
  margin-top: 0;    /* 모바일에서 과도한 마진 방지 */
}

@media (min-width: 768px) {
  .footer-hero {
    height: 31.25rem; /* md:h-[500px] */
    margin-top: 8rem; /* mt-32 = 128px */
  }
}
```

**리스크:** LOW.

---

### FIX #9 — Value Card 그림자 레이어 추가

```css
/* 기존: box-shadow: 0 8px 32px rgba(0,0,0,.1); */

.value-card {
  box-shadow:
    0 10px 15px -3px rgba(0,0,0,.10),
    0 4px  6px  -4px rgba(0,0,0,.10);
  /* Tailwind shadow-lg 정확한 매핑 */
}
```

**리스크:** LOW — 그림자 값만 교체.

---

### FIX #10 — Search Bar Pill 형태 (desktop)

```css
/* 기존: .search-bar { border-radius: 1.25rem; } */

.search-bar {
  border-radius: 1rem; /* mobile: rounded-2xl 16px */
}

.btn-search {
  border-radius: 0.75rem; /* mobile: rounded-xl */
}

@media (min-width: 768px) {
  .search-bar {
    border-radius: 9999px; /* desktop: rounded-full (pill) */
  }

  .btn-search {
    border-radius: 9999px; /* desktop: rounded-full */
  }
}
```

**리스크:** LOW — border-radius만 변경. 검색 기능 로직 무관.

---

## C. 리스크 레벨 요약

| # | Gap | CSS Fix | Risk |
|---|-----|---------|------|
| 1 | Stat card translateY overlap | `.stat-grid` translateY, `#feature` pt | **MEDIUM** |
| 2 | Hero mix-blend-multiply | `#hero-overlay` 1줄 추가 | LOW |
| 3 | Feature card 반응형 패딩 | `.feature-card` @media | LOW |
| 4 | About 섹션 모바일 spacing | 4개 섹션 margin-bottom @media | LOW |
| 5 | Anagram 패널 shadow-inner | `.anagram-visual` padding + shadow | LOW |
| 6 | Nav 모바일 패딩 | `nav` @media | LOW |
| 7 | BrandHero 모바일 패딩 | `#brand` @media | LOW |
| 8 | Footer Hero 높이 + 마진 | `.footer-hero` @media | LOW |
| 9 | Value card 그림자 | `.value-card` box-shadow | LOW |
| 10 | Search bar pill shape | `.search-bar`, `.btn-search` @media | LOW |

> **MEDIUM 리스크 #1의 근거:** `translateY(50%)`는 `.stat-grid` 자신의 렌더링된 높이에 비례하는데, 이 높이는 콘텐츠(비자 태그 수)에 따라 가변. 브라우저에서 실측 후 `clamp()` 또는 고정값으로 보정하는 2차 조정이 필요할 수 있음. 나머지 9개는 모두 LOW — HTML/JS 미접촉, 레이아웃 충돌 없음.

---

## D. 수정 대상 선택자 전체 목록

```
#hero-overlay              → mix-blend-mode: multiply 추가
nav                        → padding @media 분기
.search-bar                → border-radius @media 분기
.btn-search                → border-radius @media 분기
#brand                     → padding @media 분기 (모바일 축소)
.stat-grid                 → transform @media 분기 (핵심)
#feature                   → padding-top @media 연동
.feature-card              → padding, gap @media 분기
.anagram-visual            → padding-top/bottom 증가, box-shadow inset 추가
.anagram-section           → margin-bottom @media 분기
.start-section             → margin-bottom @media 분기
.values-section            → margin-bottom @media 분기
.roadmap-section           → margin-bottom @media 분기
#about                     → padding @media 분기
.footer-hero               → height, margin-top @media 분기
.value-card                → box-shadow 레이어 교체
```

---

## E. 변경하지 말아야 할 것

다음은 **이미 Figma와 일치하거나** 건드리면 기능이 깨지는 항목이다.

| 항목 | 이유 |
|---|---|
| `#brand-bg img` opacity, mix-blend-overlay | 이미 Figma 값과 정확히 일치 |
| `.stat-card` 개별 스타일 | 수치 일치 (padding, font-size, color) |
| `.checklist` 그라디언트 + 라디우스 | Figma와 동일 |
| `.roadmap-dot` 색상 + ring | Figma와 동일 (`#FF6B5B`, `ring-4 ring-[#FFB8A8]/40`) |
| `.roadmap-year` pill 형태 | 이미 `border-radius: 9999px` ✓ |
| `.footer-hero` `border-radius: 2.5rem` | Figma `rounded-[40px]` = 40px = 2.5rem ✓ |
| `.value-card` `aspect-ratio: 1/1` | Figma `aspect-square` ✓ |
| `.footer-hero-eyebrow` 색상 | `#7DD8B8` ✓ |
| 모든 JS 로직 | 애너그램 animation, 이미지 shuffle, scroll |
| 검색/결과/모달 기능 | Phase 9A 범위 밖 |
| `docs/CONTEST_STRATEGY.md` | 명시적 제외 |
| 색상 변수 (`:root`) | `--green`, `--coral`, `--sand`, `--border-warm` 모두 정확 |
| 로고 SVG | Figma와 동일 |
| `.logo-sub` 텍스트 | `text-[10px]` tracking-widest ✓ |

---

## F. Phase 9A 구현 순서 (권장)

> **원칙:** 임팩트 높은 것부터, 리스크 낮은 것 먼저, 의존 관계 있는 것은 묶어서.

### Wave 1 — 즉시 적용, 리스크 없음 (30분)
```
FIX #2  Hero overlay mix-blend-multiply      ← 한 줄, 즉각 분위기 변화
FIX #6  Nav 모바일 패딩                        ← @media 2줄
FIX #10 Search bar pill (desktop)            ← border-radius @media
FIX #9  Value card shadow-lg 정렬             ← box-shadow 1줄 교체
```

### Wave 2 — 반응형 spacing (1시간)
```
FIX #3  Feature card 반응형 패딩              ← @media padding/gap
FIX #4  About 서브섹션 모바일 spacing 축소    ← 4개 선택자 @media
FIX #7  BrandHero 모바일 패딩 축소            ← #brand @media
FIX #8  Footer Hero 높이 + 마진              ← .footer-hero @media
```

### Wave 3 — 섹션 간 리듬 교정 (2시간, 실측 필요)
```
FIX #5  Anagram 패널 shadow-inner + 패딩     ← 시각 확인 후 padding 미세조정
FIX #1  Stat card translateY (핵심)           ← desktop 실측 후 값 확정
        → FIX #7과 연동: #brand 패딩 → stat grid 높이 → #feature pt 순서로
```

### Wave 4 — 검증 및 스크린샷 비교
```
- 1280px desktop: hero → brand → stat card 오버랩 확인
- 375px mobile: 각 섹션 padding 과잉 없는지 확인
- Safari: backdrop-filter 렌더링 확인
- 스크롤 애니메이션 (.reveal) 정상 동작 확인
```

---

## 부록 — Figma 원본 핵심 설계 의도 메모

**BrandHero ↔ FeatureSection 연결 구조 (가장 중요한 디자인 의도):**

```
[BrandHero]
  py-24(mobile) / py-32(desktop) 충분한 높이
  ↓
[StatGrid]
  translate-y-1/2 → BrandHero 바닥에 걸쳐 아래로 float
  ← 이것이 BrandHero와 FeatureSection을 "연결"하는 시각적 장치
  ↓
[FeatureSection]
  pt-16(mobile) / pt-48(desktop) → StatGrid float 공간 확보
```

이 세 요소는 반드시 함께 조율해야 한다. 하나만 바꾸면 나머지가 어긋남.

**색상 시스템 원칙:**
- `#0EA37B` / `#085E48` — 그린 계열 (신뢰, 공식성)
- `#FF6B5B` / `#FFB8A8` — 코럴 계열 (강조, 숫자)
- `#fcfaf5` — 따뜻한 오프화이트 배경
- `#D8CAB0` — 따뜻한 베이지 보더
- `#7DD8B8` — 민트 (Footer hero eyebrow, teal accent)

이 6가지 색상 외에 신규 색상 추가 금지.
