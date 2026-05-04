# Figma Make Paradiso Handoff

## 1. Purpose

This document translates the Figma Make visual direction into safe implementation guidance for the existing Paradiso codebase.

The Figma Make output should be treated as visual reference only. Do not copy its React/Tailwind code directly.

The existing Paradiso app is a single vanilla `index.html` application with fragile search/header state behavior. Implementation must preserve existing IDs, data-action attributes, search behavior, modals, and debug instrumentation.

## 2. Visual Direction

The Figma design direction is:

**Cinematic Civic Gateway**

It presents Paradiso as a premium, trustworthy public-service gateway for Korean visa and residence information.

Core feeling:

- Cinematic
- Scenic
- Trustworthy
- Public-service oriented
- Premium but approachable
- More like a guided entry point than a database
- Less like a government portal
- Less like a generic SaaS landing page
- Less like a chatbot

## 3. Key Visual Traits From Figma

The Figma result uses:

1. Full-screen scenic Korean/Jeju-style hero background
2. Dark gradient overlay for readability
3. Large white centered Korean headline
4. Central glassmorphism search surface
5. Four translucent primary action cards
6. Compact top brand/header treatment
7. Warm premium civic/travel-service atmosphere
8. Strong first-impression landing page
9. Clear public-service trust tone

## 4. What To Borrow

Borrow these visual ideas:

- Full-screen cinematic landing hero
- Dark overlay or scenic gradient
- Large high-contrast headline
- Glass-like search container
- Translucent action cards
- More emotionally appealing brand entrance
- Stronger sense of place and public-service trust
- Cleaner hero hierarchy
- Premium visual spacing

## 5. What Not To Borrow

Do not borrow these implementation details:

- React component structure
- Tailwind classes
- motion/react animation dependency
- lucide-react dependency
- shadcn/ui component system
- Vite project structure
- Any generated router structure
- Any new build system
- Any new JavaScript dependency

The current app is not being converted to React.

## 6. Existing Code Constraints

The existing app uses:

- single `index.html`
- vanilla JavaScript
- inline CSS
- existing search state classes:
  - `body.landing`
  - `body.searching`
  - `body.searched`
- direct search debug instrumentation from PR #77:
  - `SEARCH_DEBUG_ENABLED`
  - `debugSearchState`
  - `setDirectSearchToggleState`

Do not break these.

## 7. Forbidden Regressions

Never reintroduce:

- `.landing-main`
- `.landing-evidence-panel`
- `근거 확인 흐름`
- wrapper elements around `.header-inner` children

Do not change:

- existing IDs
- existing `data-action` attributes
- existing search form behavior
- existing modal triggers
- searched-state sticky header behavior
- debugSearch behavior

## 8. Fragile Selectors To Preserve

Preserve these elements and their behavior:

- `.hero-container`
- `.header-inner`
- `.logo-area`
- `.search-wrap`
- `#searchForm`
- `#searchToggleBtn`
- `#q`
- `#xb`
- `.hero-actions`
- `.qa-main`
- `#visaManualSection`
- `[data-action="toggle-search"]`
- `[data-action="reset-to-landing"]`
- `[data-action="open-jobcode-modal"]`
- `[data-action="open-jurisdiction-modal"]`

## 9. Implementation Phases

### Phase 1: Hero-only visual reskin

Goal:
Make the landing hero visually closer to the Figma direction while preserving structure and behavior.

Allowed:

- CSS-only changes in `index.html`
- landing-only styles using `body:not(.searched)`
- gradient or background treatment
- glass-style search/action surfaces
- typography/spacing refinements

Avoid:

- HTML restructuring
- JavaScript changes
- new dependencies
- changing `data-action`

### Phase 2: Action card refinement

Goal:
Make the four major actions feel closer to translucent Figma cards.

Allowed:

- CSS for `.hero-actions`, `.qa-main`, `.hero-action-btn`
- hover/focus visual polish

Avoid:

- changing button semantics
- changing click handlers

### Phase 3: Search surface refinement

Goal:
Make `#searchForm` and `.sbar` closer to Figma's glass search surface.

Allowed:

- CSS changes to `.search-wrap`, `.sbar`, `#q`, `#xb`, `.sbar-go`

Avoid:

- changing search logic
- changing `clearSearch`
- changing direct-search behavior unless separately tested

### Phase 4: Result list polish

Goal:
Make search results feel visually integrated with the new hero direction.

Allowed:

- CSS-only changes to result cards/list

Avoid:

- changing result rendering logic

### Phase 5: Optional image asset

If a suitable local image asset exists, it may be used as a landing hero background.

If no safe local asset exists:

- use CSS gradients only
- do not hotlink external images
- document need for future image asset

## 10. Recommended CSS Direction

For Phase 1:

- Use `body:not(.searched) .hero-container` for cinematic landing treatment.
- Add a dark gradient overlay using existing pseudo-elements if possible.
- Keep `body.searched .hero-container` compact and readable.
- Make the logo/headline white or near-white only in landing state.
- Make search and action surfaces semi-transparent with blur.
- Keep searched-state styles separate.

Possible style direction:

```css
body:not(.searched) .hero-container {
  min-height: 100vh;
  color: #fff;
  background:
    linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,.55)),
    radial-gradient(circle at 20% 20%, rgba(47,94,103,.55), transparent 35%),
    radial-gradient(circle at 80% 30%, rgba(255,107,91,.25), transparent 30%),
    #10231f;
}

body:not(.searched) .sbar,
body:not(.searched) .hero-action-btn {
  background: rgba(255,255,255,.14);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,.24);
}
```
