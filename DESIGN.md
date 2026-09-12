# XDNA 2 Field Guide — 日系白底設計

## Visual direction
Japanese editorial field notes: white paper, sumi-grey ink, generous whitespace, thin rules, restrained botanical green, dusty sakura and warm sand. No neon, dark panels or heavy glows. Existing technical content, diagram meanings and interactive behavior are unchanged.

## Palette
- Canvas `#ffffff`; paper cards `#faf9f6`; subtle surface `#f8f9f6`; rules `#d9dfd9`.
- Primary text `#293331`; secondary text `#5c6662`.
- Compute / links `#37655f` on pale green `#edf4ee`.
- Memory `#80536a` on sakura `#f6edf0`.
- DMA / warning `#875d25` on sand `#f7f1e6`.
- Success `#3e674b`; small editorial stamp `#ae6d71`.
- Light color-scheme remains explicit even if OS preference is dark. Semantic token names cyan/violet/amber retained for existing inline references, but values follow the new palette.

## Typography, geometry and controls
Georgia / system CJK serif for editorial h1/h2, system sans + Noto Sans TC fallback for readable technical body, ui-monospace for code and numbers. No third-party fonts or analytics. Body 16px/1.85; h1 41px mobile, up to 66px desktop. White-background code surfaces with dark green ink. Restrained 3–10px radii, little shadow, pale bordered diagrams. Large touch controls remain at least 44px, with dark green keyboard focus rings; selected tile has an inset underline as well as color.

Mobile: 390px, 20px gutters, one column. Desktop: max wrapper 1160px with 24px gutters, split hero, three-column explanations. Breakpoint 800px; every single-column grid uses minmax(0,1fr) so code scrolls inside its container rather than widening a narrow desktop window. Sticky chapter nav has solid light background; nav, tables and code deliberately scroll horizontally within their containers.

## Verification
`python3 -m unittest discover -s tests` includes `test_light_theme.py`: rendered white background under dark OS preference, normal/hover/control/tile text contrast >=4.5:1 on representative surfaces, narrow desktop and wide desktop containment. Existing Node estimator and Playwright mobile/desktop interaction suite remain in use. Screenshots cover all chapters and interactive states. These checks are not a full accessibility audit or NPU execution proof.
