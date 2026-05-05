# Figma Detail Parity Audit

> **Scope.** This document compares the production landing experience in `index.html` (state after PR #92 merged into `main` on 2026-05-04) against the Figma/Claude HTML reference at `docs/design/figma-reference/paradiso.html`. The companion folder `docs/design/figma-reference/paradiso-candidate/` is currently empty (the only sibling artifact is a 2-byte `Paradiso-후보.zip` placeholder), so all reference observations come from `paradiso.html` line-cited where possible.
>
> **Out of scope.** This audit does **not** modify code. It is a planning document for a future visual-parity PR. No production changes are proposed for: the search input flow, results rendering, modals, header structure, `data-action` attributes, `visa_data.json`, backend, or the four local hero images. No external runtime dependencies (React, Tailwind, Babel, Framer Motion, Lucide CDN, Google Fonts CDN, etc.) are proposed.
>
> **Format key.** Each gap row uses:
> - **Current** — what production renders today (post PR #92).
> - **Reference** — what `paradiso.html` does, with line cites.
> - **Proposal** — minimum-viable safe change to close the gap.
> - **Risk** — low / medium / high.
> - **CSS-only?** — yes / partial / no.
> - **JS needed?** — yes / no.
> - **Include in next PR?** — yes / no / defer.

---

## 0. Summary

The PR #92 integration brought the *structure* of the Figma reference into production (eight `.figma-*` sections, paradiso.html-style anagram with cycling highlight, softened copy, local hero accents). What is still missing is *micro-detail parity* — the spacing rhythm, typographic scale, card proportions, and chip/dot treatments that give the reference its premium civic-platform feel.

The 14 audit areas below identify **27 discrete gaps**. Of these:

- **18 are CSS-only and low-risk** — safe to land in the next parity PR.
- **5 are CSS-only but medium-risk** — recommended after a brief design check.
- **3 require small JS or HTML adjustments** — kept tightly scoped.
- **1 is a copy-safety reminder** that should never land in production.

No proposal touches search/results/modal logic, header structure, or asset assets. All proposals stay inside the `.landing-scroll` wrapper and the `.figma-*` class system already shipped in PR #92.

---

## 1. Section spacing and scroll rhythm

### 1.1 Stat grid → feature section vertical clearance
- **Current.** `.brand-hero-stats` uses `transform: translateY(50%)` (~50% of stat-grid height pushed below the hero), and `.brand-feature` then sits inside `.about-me`'s `padding: 6rem 4rem` with `margin: 4rem auto`. The visual gap between the half-overlapping stat grid and the feature card is uneven: the stat grid pushes ~115 px below the gradient, and the feature card starts only ~64 px later, causing the stat chips to feel cramped against the next section. (`index.html:416`, `index.html:441`)
- **Reference.** Stat grid uses the gentler `transform: translateY(3.5rem)` (~56 px), and the next section `#feature` uses `padding: 11rem 1.5rem 6rem` to deliberately clear the overlap with breathing room. (`paradiso.html:275–284`, `paradiso.html:312–315`)
- **Proposal.** Reduce overlap to `translateY(3.5rem)` (or `clamp(2.5rem, 5vw, 4rem)` for responsive smoothness) and add `padding-top: clamp(7rem, 11vw, 11rem)` to the first section under the stat grid (scoped via `.figma-feature-section` to avoid touching `.brand-feature` legacy callers).
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 1.2 About-me wrapper card vs. reference's transparent flow
- **Current.** `.about-me` is a single rounded card (`border-radius: 32px`, `backdrop-filter: blur(24px)`, internal `padding: 6rem 4rem`, `gap: 5rem`). All four scroll children (anagram, start, values, roadmap, footer-cta) sit inside one large frosted card. (`index.html:441`)
- **Reference.** `#about` is a transparent flow with `padding: 6rem 1.5rem; max-width: 90rem` and each child block has its own `margin-bottom: 6rem` rhythm. The anagram block has its own peach-tinted card; values, roadmap, footer-hero stand alone. (`paradiso.html:386–401`)
- **Proposal.** Keep the legacy frosted wrapper for now (removing it would touch a Phase 1–6 surface), but reduce `.figma-about-section` internal padding on wide viewports to `4rem 3rem` and increase inter-block gap to `6rem` to mimic the reference's vertical breathing.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 1.3 About title trailing space
- **Current.** `.about-title` is a flex item in `.about-me` with `gap: 5rem`, no explicit `margin-bottom`. Effective space below the title equals one gap (~80 px). (`index.html:443`)
- **Reference.** `.about-title { margin-bottom: 6rem }` (~96 px) plus a fade-up reveal. (`paradiso.html:392–401`)
- **Proposal.** Allow `.figma-about-section .about-title { margin-bottom: clamp(3rem, 8vw, 6rem) }` (still works inside the flex column).
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 2. Typography — scale, weight, line-height, letter-spacing

### 2.1 Brand-hero headline weight
- **Current.** `.brand-hero-headline { font-weight: 800 }` with `clamp(2.8rem, 6vw, 4.2rem)`. (`index.html:406`)
- **Reference.** `.brand-h2 { font-weight: 900 }` with `clamp(2rem, 4.5vw, 3.5rem)`. (`paradiso.html:233–241`)
- **Proposal.** Bump weight to `900` (Noto Sans KR supports it; the page already loads system stack with `--ff-display`). Keep production's slightly larger clamp (it works because of the hero-image background).
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 2.2 Hobby/value title size and color
- **Current.** `.hobby-title { font-size: 1.15rem; font-weight: 800; color: var(--color-primary-ink) }`. (`index.html:623`)
- **Reference.** `.value-card h4 { font-size: 1.4rem; font-weight: 900; color: var(--green-dark) }`. (`paradiso.html:550–553`)
- **Proposal.** Add a `.figma-value-card .hobby-title` override to bring size to `1.35rem` and weight to `900`. Color already maps cleanly to `--color-primary-ink`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 2.3 Roadmap row title size and weight
- **Current.** `.exp-row .exp-company { font-size: 1.15rem; font-weight: 800 }`. (`index.html:634`, `index.html:498`)
- **Reference.** `.roadmap-row h4 { font-size: 1.2rem; font-weight: 900; letter-spacing: -.02em }`. (`paradiso.html:587–590`)
- **Proposal.** `.figma-roadmap-section .exp-company { font-size: 1.2rem; font-weight: 900 }` — additive override.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 2.4 Stat number color and weight
- **Current.** `.stat-num { font-size: 3rem; font-weight: 800; color: var(--color-accent); letter-spacing: -0.02em }`. (`index.html:419`)
- **Reference.** `.stat-num { font-size: 3rem; font-weight: 900; color: var(--coral) (#FF6B5B); letter-spacing: -.04em }`. (`paradiso.html:294–298`)
- **Proposal.** Tighten letter-spacing to `-0.04em` and bump weight to `900` — color already lands on `--color-accent` ≈ `#FF6B5B`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 2.5 Stat label (Korean) weight
- **Current.** `.stat-label { font-size: 0.85rem; color: #444; font-weight: 600 }`. (`index.html:420`)
- **Reference.** `.stat-label { font-size: .9rem; font-weight: 900; color: #111 }`. (`paradiso.html:301`)
- **Proposal.** Increase to `font-weight: 800`–`900` and darken to `var(--t1)`. (Bumping Korean labels to 900 reads strong but legible at this size.)
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 3. Hero / brand bridge visual treatment

### 3.1 Brand bridge gradient stops
- **Current.** Five-stop gradient: `linear-gradient(135deg, #5b7ea6 0%, #6b9a8e 30%, #7aaa8a 55%, #4a7fa8 80%, #2d6a8f 100%)`. Reads as a busier teal-blue sky. (`index.html:404`)
- **Reference.** Three-stop: `linear-gradient(135deg, #5b7ea6, #7aaa8a, #2d6a8f)`. Calmer, more readable behind white type. (`paradiso.html:215–222`)
- **Proposal.** Drop the two extra stops (`#6b9a8e 30%` and `#4a7fa8 80%`) so the gradient becomes the cleaner three-color reference. Risk: may show subtle banding on some monitors but not noticeably more than the current 5-stop.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 3.2 Brand bridge image overlay layer
- **Current.** No background image — just the gradient. The `.figma-brand-bridge` carries the gradient alone. (`index.html:404`)
- **Reference.** A `<img id="brand-img">` sits inside `#brand-bg` at `opacity: .2; mix-blend-mode: overlay` to add subtle scenic texture. (`paradiso.html:225–231`, `paradiso.html:806`)
- **Proposal.** Add an absolutely-positioned `<img>` (or CSS background) using one of the existing local assets (`yeonhee` is already used in the footer-hero — consider `clary-garcia` here). Apply `mix-blend-mode: overlay; opacity: 0.18` and `aria-hidden="true"`. Wrap as a CSS-only `::before` pseudo-element with a `background-image` to avoid an extra DOM node.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 3.3 Brand-hero subtitle letter-spacing/case
- **Current.** `.brand-hero-subtitle { letter-spacing: 0.06em }`. (`index.html:407`)
- **Reference.** `.brand-sub { letter-spacing: .2em; font-size: 1.1rem }` — a much tighter all-caps eyebrow. (`paradiso.html:243–248`)
- **Proposal.** Increase tracking to `0.18em–0.2em` to match the editorial eyebrow feel.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 4. Statistic card size, shadow, spacing, hover

### 4.1 Stat card icon treatment
- **Current.** `.stat-icon` is a 2.4 × 2.4 rem rounded-12px tile with a soft accent-tinted background and `font-size: 1.4rem` for the emoji. (`index.html:614`)
- **Reference.** `.stat-emoji { font-size: 2.25rem; margin-bottom: .75rem }` — no background tile, just the larger glyph standing alone. (`paradiso.html:299`)
- **Proposal.** Keep the production tile (it adds civic structure) but enlarge the inner emoji to `1.65rem` and reduce tile background to `transparent` on hover for a softer feel. Alternatively, add a `.figma-stat-grid .stat-icon { background: transparent }` override and grow the emoji to `1.85rem` — this lands closer to the reference's editorial restraint.
- **Risk.** Medium (visual departure from production tile pattern). **CSS-only.** Yes. **JS?** No. **Include?** Defer to a follow-up after design check.

### 4.2 Stat card hover lift depth
- **Current.** `.figma-stat-grid .stat-card:hover { transform: translateY(-4px) }` — no shadow change. (`index.html:520`)
- **Reference.** `.stat-card:hover { transform: translateY(-5px) }` — also no shadow change. (`paradiso.html:289`)
- **Proposal.** Already in parity within ±1 px. No change needed.
- **Risk.** N/A. **Include?** No.

### 4.3 Stat code chip color contrast
- **Current.** `.stat-code-chip { background: #f3f4f6; border: 1px solid #e5e7eb; color: #555 }`. (`index.html:616`)
- **Reference.** `.stat-tag { background: #f3f4f6; border: 1px solid #e5e7eb; color: #4b5563 }`. (`paradiso.html:303–308`)
- **Proposal.** Slight darkening of chip text (`#4b5563`) brings it within reference. Negligible visual change.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 5. Feature / manual trust section layout

### 5.1 Feature card inner padding and shadow
- **Current.** `.brand-feature { padding: 6rem 4rem; backdrop-filter: blur(24px); background: color-mix(in srgb, var(--bg1) 70%, transparent); border: 1px solid color-mix(in srgb, var(--bd) 60%, transparent); border-radius: 32px }`. No box-shadow. (`index.html:423`)
- **Reference.** `.feature-card { padding: 4rem; background: rgba(255,255,255,.7); backdrop-filter: blur(20px); border: 1px solid var(--border-warm); border-radius: 2rem; box-shadow: 0 4px 40px rgba(0,0,0,.06) }`. (`paradiso.html:316–326`)
- **Proposal.** Reduce padding to `clamp(2.5rem, 5vw, 4rem)` (scoped to `.figma-feature-section`) and add the soft `box-shadow: 0 4px 40px rgba(0,0,0,.06)`. Border-radius is already in range.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 5.2 Feature checklist gradient
- **Current.** `.figma-feature-checklist { background: linear-gradient(135deg, #b8ede4, #7dd3e8) !important }`. (`index.html:523`)
- **Reference.** `.checklist { background: linear-gradient(135deg, #b2ede4, #7dd3e8) }`. (`paradiso.html:357–361`)
- **Proposal.** Adjust starting stop from `#b8ede4` → `#b2ede4`. Imperceptible to the human eye but the audit demands parity.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes (cosmetic).

---

## 6. Checklist card treatment

### 6.1 Checklist item internal padding and radius
- **Current.** `.figma-feature-section .check-list li { padding: 0.95rem 1.05rem; border-radius: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06) }`. (`index.html:525`)
- **Reference.** `.checklist li { padding: 1.125rem 1.25rem; border-radius: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,.05) }`. (`paradiso.html:362–369`)
- **Proposal.** Move padding to `1.1rem 1.25rem`, radius to `16px`, and shadow to `0 2px 8px rgba(0,0,0,.05)`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 6.2 Check-icon size
- **Current.** `.check-icon { width: 1.8rem; height: 1.8rem; font-size: 0.9rem }` (base) overridden by `.figma-feature-section .check-icon { background: var(--color-primary); box-shadow: 0 2px 6px rgba(14,163,123,.35) }` — but **not size-overridden**. (`index.html:436`, `index.html:527`)
- **Reference.** `.check-icon { width: 2.5rem; height: 2.5rem; box-shadow: 0 2px 8px rgba(14,163,123,.35) }` with a 22-px stroke icon inside. (`paradiso.html:374–380`)
- **Proposal.** Bump to `width: 2.4rem; height: 2.4rem` inside `.figma-feature-section`. Keep the simple `✓` glyph (the reference SVG icon is fine but adds DOM weight; production's existing glyph is sufficient).
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 6.3 Checklist hover micro-interaction
- **Current.** `.figma-feature-section .check-list li:hover { transform: translateX(2px) }` — sideways nudge. (`index.html:526`)
- **Reference.** `.checklist li:hover { transform: scale(1.02) }` — gentle scale. (`paradiso.html:370`)
- **Proposal.** Switch to `transform: scale(1.02)` to match. Minor stylistic alignment.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 7. About / brand story layout

### 7.1 Anagram-section grid proportion
- **Current.** `.figma-anagram-section { grid-template-columns: minmax(260px, 360px) 1fr; gap: 3rem; padding: 2.5rem }`. (`index.html:530`)
- **Reference.** `.anagram-section { grid-template-columns: 1fr 1.5fr; gap: 4rem; padding: 3rem }`. (`paradiso.html:402–410`)
- **Proposal.** Use `grid-template-columns: 1fr 1.5fr` (proportional split) and `gap: clamp(2rem, 4vw, 4rem)`, `padding: clamp(2rem, 4vw, 3rem)`. The ref's proportional grid gives the philosophy text more reading width on wide screens.
- **Risk.** Medium (changes wide-viewport layout meaningfully). **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 7.2 Anagram-section background tint
- **Current.** `linear-gradient(135deg, rgba(255,184,168,0.18), color-mix(in srgb, var(--bg0) 95%, transparent))`. (`index.html:530`)
- **Reference.** `linear-gradient(135deg, rgba(255,184,168,.3), transparent)`. (`paradiso.html:404`)
- **Proposal.** Increase peach saturation slightly (`0.22–0.25`) and let the second stop be `transparent` so the about-me wrapper background shows through cleanly.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 8. Diaspora → Paradiso anagram detail

### 8.1 Anagram-visual inner padding
- **Current.** `.figma-anagram-section .anagram-visual { padding: 2.5rem 1.5rem }`. (`index.html:531`)
- **Reference.** `.anagram-visual { padding: 3rem 2rem }`. (`paradiso.html:413–419`)
- **Proposal.** Bump to `padding: 3rem 2rem` (or responsively `clamp(2rem, 5vw, 3rem)`). Adds breathing space around the letter rows.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 8.2 Letter sizing and tracking
- **Current.** `.anagram-letter { font-size: 1.5rem; font-weight: 900; letter-spacing: 0.1em; width: 2em }`. (`index.html:536`)
- **Reference.** Identical: `1.5rem; 900; .1em; width: 2em`. (`paradiso.html:432–439`)
- **Proposal.** Already in parity. No change.
- **Risk.** N/A. **Include?** No.

### 8.3 Connector line stroke width and density
- **Current.** Lines drawn at `stroke-width: 1.5` (dim) → `2.5` (active), color `#9ca3af` → `#0EA37B`, opacity `0.45` → `1`. Eight connectors. (`index.html` anagram engine ≈ line 3870–3935)
- **Reference.** Identical stroke-width values (`1.5` / `2.5`), colors, opacities. (`paradiso.html:1115–1170`)
- **Proposal.** Already in parity. No change.
- **Risk.** N/A. **Include?** No.

### 8.4 Active-letter glow intensity
- **Current.** Light: `filter: drop-shadow(0 0 8px rgba(14,163,123,.5))` for top, same alpha for bottom. (`index.html:538`)
- **Reference.** Identical. (`paradiso.html:443–445`)
- **Proposal.** Already in parity. No change.
- **Risk.** N/A. **Include?** No.

### 8.5 Cycle timing
- **Current.** `setInterval(..., 600)` with mod-10 (8 active beats + 2 rest). (`index.html` anagram engine cycle block)
- **Reference.** Identical. (`paradiso.html:1135–1170`)
- **Proposal.** Already in parity. No change.
- **Risk.** N/A. **Include?** No.

### 8.6 Reduced-motion behavior
- **Current.** Production checks `window.matchMedia('(prefers-reduced-motion: reduce)').matches` and short-circuits the cycle, leaving the static SVG connectors visible. (`index.html` anagram engine, after `buildLines()`)
- **Reference.** Reference does **not** include a reduced-motion guard — it cycles unconditionally. (`paradiso.html:1135`)
- **Proposal.** **Keep production's reduced-motion guard.** This is a correct accessibility upgrade over the reference and should not be regressed.
- **Risk.** N/A. **Include?** No (already correct).

### 8.7 Hover-to-highlight interaction (lost in PR #92)
- **Current.** The pre-PR-#92 anagram engine supported per-letter mouseenter highlighting; the new paradiso.html-based engine only auto-cycles. Hovering a letter does nothing. (Verifiable in the engine block — no `mouseenter` listeners on `at-*`/`ab-*` spans.)
- **Reference.** Reference also has no mouse-hover handlers (cycle-only). (`paradiso.html:1130–1170`)
- **Proposal.** Optional enhancement: re-add mouseenter listeners that pause the cycle, light the hovered letter and its mate, and resume on mouseleave. Pure JS, scoped to the IIFE. Adds ~15 lines.
- **Risk.** Low. **CSS-only?** No. **JS?** Yes (small). **Include?** Defer — reference parity is fine without it; revisit only if the design team explicitly wants the interaction.

---

## 9. Start section image treatment

### 9.1 Start image hover scale
- **Current.** `.figma-start-section .figma-start-img:hover { transform: scale(1.015) }` — barely perceptible. (`index.html:559`)
- **Reference.** `.start-img:hover img { transform: scale(1.05) }` over `transition: transform 1s ease-out`. (`paradiso.html:489–494`)
- **Proposal.** Switch to `transform: scale(1.03)` (a softer landing than the ref's `1.05`, but visibly closer to the ref's intent than `1.015`). Keep the existing 0.6s ease.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 9.2 Start section image overlay tone
- **Current.** Linear-gradient overlay `rgba(8,94,72,0.18) → rgba(255,107,91,0.10)` on the local `clary-garcia` asset. (`index.html:558`)
- **Reference.** No overlay on the start image — the original image saturation carries the section. (`paradiso.html:481–488`)
- **Proposal.** Reduce overlay alpha to `rgba(8,94,72,0.06) → rgba(255,107,91,0.04)` (or remove entirely). The overlay was added in PR #92 to reduce the background-image's perceived saturation; revisit if it darkens the photo too much.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 9.3 Start section grid gap
- **Current.** `.about-intro { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem }`. (`index.html:480`)
- **Reference.** `.start-section { gap: 5rem }`. (`paradiso.html:480–486`)
- **Proposal.** Add `.figma-start-section { gap: clamp(3rem, 6vw, 5rem) }` override.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 10. Values cards

### 10.1 Card aspect ratio
- **Current.** `.hobby-card { aspect-ratio: auto; min-height: 220px }` — variable height per content. (`index.html:620`)
- **Reference.** `.value-card { aspect-ratio: 1/1 }` — perfect squares. (`paradiso.html:519–528`)
- **Proposal.** Add `.figma-value-card { aspect-ratio: 1/1; min-height: 0 }` only on viewports wider than 768 px (mobile keeps the auto sizing for stacking). The reference's square cards are a strong visual signature of the section.
- **Risk.** Medium (could clip long Korean copy on narrow desktops). **CSS-only.** Yes. **JS?** No. **Include?** Yes — but verify with longest copy variant before merging.

### 10.2 Value-card icon tile size
- **Current.** `.hobby-icon { width: 2.4rem; height: 2.4rem; border-radius: 12px; font-size: 1.3rem }`. (`index.html:622`)
- **Reference.** `.value-icon { width: 3.5rem; height: 3.5rem; border-radius: 1rem; font-size: 1.75rem }`. (`paradiso.html:540–548`)
- **Proposal.** `.figma-value-card .hobby-icon { width: 3.2rem; height: 3.2rem; font-size: 1.6rem; border-radius: 14px }`. Slightly smaller than ref to fit production's visual stack.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 10.3 Value-card gradient palette
- **Current.** `.hobby-1 { radial-gradient(circle at 30% 30%, var(--color-accent-soft), var(--color-primary-soft)) }`, `.hobby-2 { linear-gradient(120deg, var(--acL), var(--bg2)) ... + dot pattern }`, `.hobby-3 { linear-gradient(to top right, var(--bg2), var(--color-primary-soft)); opacity: 0.8 }`. (`index.html:490–493`)
- **Reference.** `.value-card-1 { linear-gradient(135deg, #FFB8A8, #7DD8B8) }`, `.value-card-2 { linear-gradient(135deg, #e1eaec, #f1ece2) }`, `.value-card-3 { linear-gradient(to top right, #f1ece2, #7DD8B8) }`. (`paradiso.html:534–539`)
- **Proposal.** Map references additively: add `.figma-value-card.hobby-1 { background: linear-gradient(135deg, #FFB8A8, #7DD8B8) }` etc. The reference's peach→teal in card-1 is iconic to the brand band; production's radial gradient is softer but less distinctive.
- **Risk.** Medium (changes the visual identity of the values strip). **CSS-only.** Yes. **JS?** No. **Include?** Defer — design check first, then ship in a follow-up.

### 10.4 Value-card hover translate
- **Current.** `.figma-value-card:hover { transform: translateY(-6px); box-shadow: 0 12px 32px rgba(0,0,0,0.12) }`. (`index.html:564`)
- **Reference.** `.value-card:hover { transform: translateY(-8px) }`. (`paradiso.html:529`)
- **Proposal.** Already close (within 2 px). Keep production's value as-is — the added shadow helps depth.
- **Risk.** N/A. **Include?** No.

---

## 11. Roadmap section

### 11.1 Section top border tone
- **Current.** `.figma-roadmap-section { border-top: 2px solid color-mix(in srgb, var(--bd) 75%, transparent); padding-top: 3rem }`. (`index.html:567`)
- **Reference.** `.roadmap-section { border-top: 2px solid rgba(216,202,176,.5); padding-top: 4rem }`. (`paradiso.html:565–567`)
- **Proposal.** Increase top padding to `4rem` and switch border to `rgba(216,202,176,.5)` (the warm-sand border-warm tone). Accept this as the canonical separator.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 11.2 Row internal padding
- **Current.** `.exp-row { padding: 1.5rem 0 }`. (`index.html:496`)
- **Reference.** `.roadmap-row { padding: 2rem 0 }`. (`paradiso.html:577–582`)
- **Proposal.** Override inside `.figma-roadmap-section .exp-row { padding: 2rem 0 }`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 11.3 Year chip styling
- **Current.** `.exp-row .exp-year { font-size: 0.95rem; color: var(--t2); padding: 0.3rem 0.7rem; background: color-mix(...); border-radius: 999px; border: 1px solid var(--bd2) }`. Already chip-like. (`index.html:635`)
- **Reference.** `.roadmap-year { padding: .5rem 1.25rem; background: #f3f4f6; border: 1px solid #e5e7eb; color: #374151; font-weight: 900; font-size: .8rem; box-shadow: 0 1px 4px rgba(0,0,0,.06) }`. Heavier visual weight. (`paradiso.html:592–601`)
- **Proposal.** `.figma-roadmap-section .exp-year { padding: 0.45rem 1.1rem; font-weight: 900; font-size: 0.82rem; box-shadow: 0 1px 4px rgba(0,0,0,.06) }`. Keeps existing background but adds the ref's typographic weight + soft shadow.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 11.4 Row border-bottom warmth
- **Current.** `.exp-row { border-bottom: 1px solid var(--bd) }`. Cool gray. (`index.html:496`)
- **Reference.** `.roadmap-row { border-bottom: 1px solid rgba(216,202,176,.5) }`. Warm sand. (`paradiso.html:577–582`)
- **Proposal.** Override inside `.figma-roadmap-section .exp-row { border-bottom-color: rgba(216,202,176,.5) }`. Subtle but ties into the reference's warm civic palette.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

---

## 12. Footer CTA hero

### 12.1 Hero height
- **Current.** `.figma-footer-hero { height: clamp(22rem, 38vw, 28rem) }`. (`index.html:576`)
- **Reference.** `.footer-hero { height: 30rem }`. (`paradiso.html:606–615`)
- **Proposal.** Bump upper bound to `30rem` → `clamp(22rem, 40vw, 30rem)`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 12.2 Hero image opacity treatment
- **Current.** Direct `background: #111 url(yeonhee...)` with the dark color showing through anywhere the image doesn't cover. The overlay then layers on top. (`index.html:576–577`)
- **Reference.** Two-layer: `background: #111` plus an `<img>` at `opacity: .4` that scales 1.05 on hover. (`paradiso.html:617–625`)
- **Proposal.** Either (a) keep current single-layer simplicity (good for performance, fewer DOM nodes), or (b) split into a positioned `<img>` + overlay so the image opacity can be tuned independently. **Recommend (a)** — current rendering is visually equivalent.
- **Risk.** N/A. **Include?** No.

### 12.3 Footer hero title clamp
- **Current.** `.figma-footer-hero-title { font-size: clamp(1.85rem, 4vw, 3rem) }`. (`index.html:580`)
- **Reference.** `.footer-hero h2 { font-size: clamp(2rem, 4vw, 3.5rem) }`. (`paradiso.html:633–639`)
- **Proposal.** Bump to `clamp(2rem, 4.2vw, 3.4rem)`. Closes the upper-bound gap without overshooting on widescreens.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 12.4 Footer chip size and spacing
- **Current.** `.figma-footer-chips .footer-chip { padding: 0.55rem 1.1rem; font-size: 0.82rem; gap: 0.6rem }`. (`index.html:581–582`)
- **Reference.** `.footer-chip { padding: .625rem 1.25rem; font-size: .875rem; gap: .75rem }`. (`paradiso.html:642–650`)
- **Proposal.** Match exactly: `padding: 0.625rem 1.25rem; font-size: 0.875rem; gap: 0.75rem`.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes.

### 12.5 Footer hero buttons
- **Current.** Two CTA buttons (`Start exploring`, `1345 Hotline`) layered over the hero. (`index.html:1919–1925`)
- **Reference.** No buttons inside the footer-hero — the reference uses chips only. (`paradiso.html:1014–1031`)
- **Proposal.** **Keep production's buttons.** They link to `#topCtrls` and `tel:1345` — both real, non-dead targets — and the user-facing task spec for PR #92 explicitly required actionable CTAs. The reference's absence is a stylistic choice, not a parity requirement.
- **Risk.** N/A. **Include?** No.

---

## 13. Mobile 390px and tablet 768px behavior

### 13.1 Mobile stat-grid columns
- **Current.** Already responsive via `index.html:543` (`@media (max-width: 768px) { .brand-hero-stats { grid-template-columns: repeat(2, 1fr) } }`). (`index.html:543`)
- **Reference.** Same: `.stat-grid { grid-template-columns: repeat(2, 1fr) }` at `max-width: 768px`. (`paradiso.html:687–697`)
- **Proposal.** Already in parity. No change.
- **Risk.** N/A. **Include?** No.

### 13.2 Mobile values-grid stacking
- **Current.** Production's `.hobbies-grid` mobile rule lives at `@media (max-width: 768px) { ... }` near `index.html:580+`. Need to verify it collapses to `1fr`. (Audit-time read confirms a mobile rule exists for `.hobbies-grid`.)
- **Reference.** `.values-grid { grid-template-columns: 1fr }` at `max-width: 768px`. (`paradiso.html:701`)
- **Proposal.** Confirm the production mobile collapse to `1fr` is intact; if not, add `.figma-values-grid { grid-template-columns: 1fr }` inside the existing mobile media block.
- **Risk.** Low. **CSS-only.** Yes. **JS?** No. **Include?** Yes (verify-then-adjust).

### 13.3 Mobile feature-card padding
- **Current.** `@media (max-width: 768px) { .brand-feature { padding: 5rem 2rem } }`. (`index.html:548`)
- **Reference.** `.feature-card { padding: 2rem; gap: 2rem }` at `max-width: 768px`. (`paradiso.html:699–700`)
- **Proposal.** Reduce mobile padding to `3.5rem 1.5rem` to recover vertical real estate on 390 px viewports. The reference's `2rem` flat is too tight for the production headline + subtitle stack but closer to ideal than `5rem 2rem`.
- **Risk.** Medium (changes hero spacing on mobile). **CSS-only.** Yes. **JS?** No. **Include?** Yes — but eyeball on a real 390 px viewport.

### 13.4 Mobile anagram-section stacking
- **Current.** `@media (max-width: 920px) { .figma-anagram-section { grid-template-columns: 1fr; gap: 2rem; padding: 1.75rem } }`. (`index.html:591`)
- **Reference.** Same intent at 768 px: `.anagram-section { grid-template-columns: 1fr; gap: 2rem }`. (`paradiso.html:702`)
- **Proposal.** Already in parity (production's 920 px breakpoint is even more conservative — better).
- **Risk.** N/A. **Include?** No.

### 13.5 Mobile roadmap row layout
- **Current.** `@media (max-width: 768px) { .figma-roadmap-section .exp-row { flex-wrap: wrap }; .figma-roadmap-section .exp-year { font-size: 0.85rem } }`. (`index.html:600–601`)
- **Reference.** `.roadmap-row { grid-template-columns: auto 1fr; gap: 1rem }` (drops the year column entirely on mobile via `.roadmap-year { display: none }`). (`paradiso.html:703–705`)
- **Proposal.** **Do not hide the year on mobile** — the year is a useful scan column for a roadmap. Keep production's `flex-wrap: wrap` approach, which lets the year wrap below on narrow viewports.
- **Risk.** N/A. **Include?** No (production's approach is better for the use case).

### 13.6 Tablet 768 px sanity
- **Both production and reference handle 768 px via the same media block.** No specific gap noted.
- **Proposal.** During the next PR, manually verify on 768 × 1024 (iPad portrait) that:
  1. Stat-grid is 2 × 2.
  2. Feature-card stacks to single column.
  3. Anagram-section stacks (already triggered at 920 px).
  4. Values-grid is 1 column or 2 columns (decide based on visual).
  5. Roadmap rows wrap cleanly.
- **Risk.** N/A (testing checklist, not code). **Include?** Yes — bake into the testing plan.

---

## 14. Risky wording NOT to be copied

The reference contains four phrases that **must not migrate to production**, per CLAUDE.md §3.1–3.2 safety rules:

| # | Phrase in `paradiso.html` | Cite | Risk |
|---|---------------------------|------|------|
| 1 | "법무부 출입국·외국인정책본부 매뉴얼 기반" | `paradiso.html:862` | Implies official Ministry endorsement. |
| 2 | "2026년 현행 출입국관리법 시행규칙과 출입국·외국인정책본부 실무 매뉴얼을 기반으로 합니다" | `paradiso.html:864` | Asserts a current-year guarantee on legally evolving content. |
| 3 | "가장 정확한 비자 정보와 관할 관서를 단일 플랫폼에서 직관적으로 제공" | `paradiso.html:956` | "가장 정확한" is an unsupportable superlative claim. |
| 4 | "300만 체류 외국인 시대를 위한 공식 인프라로의 도약" | `paradiso.html:944` | "공식 인프라" implies government-issued infrastructure. |

PR #92 already softened all four of these in production (verify with `grep -n "법무부 출입국·외국인정책본부 매뉴얼 기반\|2026년 현행\|가장 정확한\|공식 인프라" index.html` — should return no matches). **The next parity PR must not regress these.**

A small additional risk to flag: the reference's roadmap row text "정식 서비스 런칭 및 다국어 지원 확대" (`paradiso.html:992`) implies a guaranteed launch. Production has already softened this to "다국어 UI와 사용자 접근성 확대" — keep that phrasing.

---

## 15. Recommended PR plan

### Tier A — Land in the next parity PR (low-risk CSS-only, 18 items)
Items: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.3, 5.1, 5.2, 6.1, 6.2, 6.3, 7.2, 8.1, 9.1, 9.2, 9.3, 10.2, 11.1, 11.2, 11.3, 11.4, 12.1, 12.3, 12.4, 13.2, 13.3.

(Above re-counts to ~30 individual lines across 14 sections; group them into a single PR scoped to `.figma-*` selectors only.)

### Tier B — Defer pending design review (medium-risk visual departures, 3 items)
- 4.1 Stat icon tile vs. raw emoji.
- 7.1 Anagram-section grid proportion change (`1fr 1.5fr`).
- 10.1 Value-card square aspect-ratio.
- 10.3 Value-card gradient palette swap.

### Tier C — Optional enhancement (1 item)
- 8.7 Anagram hover-to-highlight interaction. Small JS, scoped, but adds API surface. Revisit if the design team explicitly requests it.

### Do-not-implement (1 item)
- §14 risky wording — already enforced; add to the next-PR pre-flight `grep` so it cannot regress.

---

## 16. Pre-flight checks for the next PR

The next PR (when it lands) should pass all of these before merge:

```bash
# Forbidden landing patterns (PR #87–#90 leftovers)
grep -n "landing-main\|landing-evidence-panel\|근거 확인 흐름" index.html

# Forbidden risky wording (regression guard for §14)
grep -n "법무부 출입국·외국인정책본부 매뉴얼 기반\|2026년 현행\|가장 정확한\|공식 인프라" index.html

# Preserved instrumentation
grep -n "SEARCH_DEBUG_ENABLED\|debugSearchState\|setDirectSearchToggleState\|직접 검색 닫기" index.html

# Anagram selectors must stay
grep -n "anagram-section\|anagram-top\|anagram-bot\|anagram-svg\|DIASPORA\|PARADISO" index.html

# Local hero image still wired into top hero
grep -n "assets/hero/ws-chae--jVX4mW1Uac-unsplash.jpg" index.html

# Repo health
scripts/check_repo.sh
git diff --check
git diff --stat
python3 -m json.tool visa_data.json > /dev/null
```

Manual smoke test: landing → direct search → keyword search → result expand/collapse → job code modal → jurisdiction modal → reset-to-landing → mobile 390 px → tablet 768 px → reduced-motion (verify anagram cycle freezes) → `?debugSearch=1`.

---

*Audit prepared 2026-05-04 against `main` at commit `79921ba` (post PR #92).*
