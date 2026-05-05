# LAZYWEB_JACKIE_REFERENCE_ANALYSIS

## 1) Executive summary

- **Lazyweb availability in this Codex environment:** **Unavailable** at analysis time.
  - The `codex` CLI was not available in PATH.
  - Active Codex config exposed only `make_pr` MCP server; Lazyweb MCP tools were not present.
  - No runnable `lazyweb_health` / `lazyweb_search` tools were available in this session.
- Because Lazyweb was unavailable, this document does **not** claim direct behavioral observations from `https://jackiezhang.co.za/`.
- This Phase 9B-1 document therefore provides a **safe translation framework** for Paradiso using local project context (Figma parity docs + current `index.html` structure), and marks web-reference validation as a follow-up in an MCP-capable client (e.g., Claude Code).

**What Paradiso can learn (taste-level, non-cloning):**
- stronger editorial rhythm between sections,
- fewer but more memorable “signature moments,”
- tactile composition without losing civic trust,
- controlled asymmetry with strict readability constraints.

**What must not be copied:**
- personal portfolio voice/structure,
- personal storytelling motifs,
- exact layouts/copy/images/branding elements,
- playful motifs that reduce public-service trust.

---

## 2) Borrowable design principles (translation matrix)

> Note: “Reference behavior” below is framed as **target taste category** only (not a claimed direct scrape), due Lazyweb unavailability.

### A. Section rhythm
- **Reference behavior (taste target):** Alternating dense/light bands with intentional pause zones.
- **Paradiso translation:** Keep existing landing sequence, but tune vertical cadence so each block has clear entrance, content body, and exit breathing room.
- **CSS-only implementation candidate:** Adjust per-section `padding-block`, inter-section margins, and card inner spacing tokens only.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### B. Short strong editorial statements
- **Reference behavior (taste target):** Brief, high-confidence headings with restrained support copy.
- **Paradiso translation:** Use concise civic-language headlines (“what users can do now”), avoid portfolio-style personality copy.
- **CSS-only implementation candidate:** Typographic hierarchy refinements (weight/size/tracking/line-height), no content architecture changes.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### C. Tactile card/image composition
- **Reference behavior (taste target):** Soft depth, layered surfaces, subtle material cues.
- **Paradiso translation:** Preserve trust-first UI; apply restrained shadows, borders, and warm-neutral layering to existing cards.
- **CSS-only implementation candidate:** Border alpha, shadow softness, radius normalization, background tint balance.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### D. Organic but controlled asymmetry
- **Reference behavior (taste target):** Slightly off-center composition that still reads structured.
- **Paradiso translation:** Allow asymmetric accent alignment in hero/bridge/feature only; keep data-heavy sections highly ordered.
- **CSS-only implementation candidate:** Grid column ratios, offset media blocks, controlled transforms (small values only).
- **Risk level:** Medium.
- **Phase 9B-2:** Yes (with screenshot review).

### E. Texture / grain usage
- **Reference behavior (taste target):** Very light texture for warmth.
- **Paradiso translation:** Optional subtle grain overlays only where readability remains high and contrast passes.
- **CSS-only implementation candidate:** Low-opacity pseudo-element texture overlay in decorative regions only.
- **Risk level:** Medium.
- **Phase 9B-2:** Yes (design review first).

### F. Hover / microinteraction restraint
- **Reference behavior (taste target):** Minimal motion; tactile not flashy.
- **Paradiso translation:** Keep quick, small, legible interactions in non-critical decorative cards only.
- **CSS-only implementation candidate:** unify hover transforms to tiny scale/lift, simplify transition timing.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### G. Whitespace and density
- **Reference behavior (taste target):** Generous whitespace around key statements, denser detail blocks later.
- **Paradiso translation:** Front-load clarity (hero/search gateway), keep detail density in trust/value/roadmap with chunked scannability.
- **CSS-only implementation candidate:** spacing tokens, max-width tuning, paragraph measure control.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### H. Mobile stacking
- **Reference behavior (taste target):** Strong single-column narrative with clear priority order.
- **Paradiso translation:** Keep existing content order; reduce ornamental overlap; prioritize search and trust cues early.
- **CSS-only implementation candidate:** breakpoint-specific stacking, gap tuning, card compaction.
- **Risk level:** Low.
- **Phase 9B-2:** Yes.

### I. Image-card storytelling
- **Reference behavior (taste target):** Imagery supports narrative beats rather than decoration overload.
- **Paradiso translation:** Use existing local assets to reinforce civic journey moments; avoid personality-centric portfolio framing.
- **CSS-only implementation candidate:** image cropping ratio consistency, overlay gradients, caption spacing.
- **Risk level:** Medium.
- **Phase 9B-2:** Yes (review with screenshots).

### J. Brand signature moments
- **Reference behavior (taste target):** One or two memorable brand interactions.
- **Paradiso translation:** Keep anagram as the signature moment; avoid adding multiple playful motifs.
- **CSS-only implementation candidate:** refine anagram visual polish only (spacing/contrast/glow subtlety), no logic changes.
- **Risk level:** Medium.
- **Phase 9B-2:** Yes (visual-only).

---

## 3) Do-not-copy list

Paradiso must **not** replicate:
- personal portfolio tone,
- personal biography structure,
- exact layouts,
- exact text,
- exact images/assets,
- over-playful doodles,
- casual jokes that weaken civic trust.

Additionally:
- do not imitate personal branding marks,
- do not mimic distinctive portfolio narrative arcs,
- do not transfer stylistic quirks that reduce clarity for visa/residence guidance.

---

## 4) Section-by-section Paradiso recommendations

### Hero / search gateway
- Keep search clarity and instant intent legibility as first priority.
- Editorial tone should be concise and calm, not self-promotional.
- Use spacing and typography to separate “ask” (search) from “assistive options” without motion-heavy effects.

### Brand / stat bridge
- Preserve trust signal: quantified scope + official-source awareness.
- Refine visual transitions (gradient/spacing/depth) to feel premium but not ornamental.
- Keep stat cards clear and quickly scannable.

### Feature / trust section
- Emphasize reliability and guidance workflow.
- Use card hierarchy and icon restraint to prevent visual noise.
- Maintain checklist readability over novelty.

### Anagram brand story
- Treat as one deliberate signature moment.
- Keep semantics civic: transformation toward service clarity, not personal narrative.
- Limit embellishments; preserve accessibility and reduced-motion behavior.

### Start section
- Improve first-action confidence through spacing hierarchy and button emphasis.
- Keep language task-oriented (what user can do now).

### Values
- Maintain warm-human voice while preserving institutional trust.
- Use consistent card rhythm and simple emphasis cues.

### Roadmap
- Keep sequence readable as service evolution timeline.
- Favor structured typography and controlled density over decorative complexity.

### Footer CTA
- End with clear next steps and trust reinforcement.
- Prioritize clarity and consistency over novelty patterns.

---

## 5) CSS-only Phase 9B-2 candidates

### Low risk (can implement next)
- Global section rhythm tuning (padding/margins/gaps).
- Heading/body hierarchy refinements (weight, measure, line-height).
- Card surface consistency (radius, border contrast, soft shadows).
- Hover restraint normalization (small unified motion).
- Mobile spacing compaction at 390px/768px.

### Medium risk (needs screenshot/design review)
- Controlled asymmetry in brand/feature compositions.
- Subtle texture/grain overlays in decorative zones.
- Image-card emphasis and crop behavior adjustments.
- Anagram visual polish (contrast/spacing/glow intensity only).

### High risk (defer)
- Any change that could alter information architecture semantics.
- Any change that may reduce civic trust tone or readability.
- Any motion/interaction expansion beyond current restrained behavior.

---

## 6) Anagram guidance (visual-only for now)

- Keep current anagram logic untouched in Phase 9B-1.
- For Phase 9B-2, only adjust visual aspects (spacing, contrast harmony, emphasis balance) via CSS where possible.
- **Deferred (not now):** Any JS-level timing/state behavior changes require a separate review pass in Phase 9C.

---

## 7) Mobile guidance (390px and 768px)

### 390px
- Prioritize search gateway legibility above decorative layering.
- Collapse multi-column cards to single column with increased vertical rhythm.
- Reduce ornamental offsets/overlaps that can feel cramped.
- Keep CTA hit areas robust and copy concise.

### 768px
- Use two-column layouts selectively for comprehension, not density maximization.
- Maintain clear section boundaries and consistent card heights where practical.
- Preserve the anagram as a compact highlight, not a dominant block.

---

## 8) Suggested PR sequence

1. **Phase 9B-2:** CSS-only tasteful refinement pass (low-risk + reviewed medium-risk items).
2. **Phase 9C:** Anagram precision pass (only if visual QA indicates need; JS behavior changes explicitly gated).
3. **Phase 10:** Logo asset integration and final brand-system tightening.

---

## Lazyweb follow-up recommendation

Because Lazyweb was unavailable in this Codex environment, re-run the reference research in **Claude Code** (or another MCP-capable client with confirmed Lazyweb tools) before finalizing medium-risk stylistic decisions.

Minimum verification checklist for that rerun:
- confirm `lazyweb_health` available,
- confirm `lazyweb_search` available,
- run targeted reference queries and archive findings into an addendum,
- keep outputs principle-based and anti-cloning.
