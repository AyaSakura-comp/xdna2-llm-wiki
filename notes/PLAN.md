# XDNA 2 Architecture to Programming Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Download traceable open-source XDNA2 compiler sources and architecture references, explain their actual numeric and GEMM capabilities in a responsive Traditional Chinese website.
**Architecture:** Static self-contained HTML/CSS/JS with source-linked teaching sections, interactive device map, dtype/MMA selector and a bounded working-set calculator. Research snapshots and SHA256 manifests stay separate from published site. No driver/system changes, no unrequested hardware benchmarks.
**Tech Stack:** Python acquisition/validation, vanilla HTML/CSS/JS, node:test for calculator, Playwright/browser for rendered checks.

## Tasks
1. Acquire `/home/chihmin/xdna2-lab/sources/{mlir-aie,llvm-aie,mlir-air,Triton-XDNA,aie_api}` at recorded SHAs; keep LLVM sparse scope explicit and record uninitialized submodules. Snapshot primary docs in `documents/`, SHA256 + source URLs in `manifest.json`.
2. Independently audit types/MMA using headers/tests in `notes/type-mma-audit.md`; parent audits compiler/frontend/programming claims. Compare IRON, Triton/AIR, IREE without claiming a universal benchmark winner.
3. Create `DESIGN.md`: dark editorial technical guide, cyan compute / violet memory / amber runtime, responsive at 390 and 1440.
4. RED: `node --test tests/model.test.cjs` tests dtype geometry, workset bytes, divisibility warnings, invalid input. `python3 -m unittest discover -s tests` tests sections/links/artifacts. Confirm missing features fail.
5. GREEN: `site/model.js`, `site/index.html`: teach architecture, type matrix, mmul and packing, compiler pipeline, exact checked-source IRON/Triton paths and code, profiling plan, limitations, references/downloads. Integrate audited claims only.
6. Validate and inspect all section anchors and interactive states at mobile/desktop, collect screenshots, no overflow or console exceptions. Record evidence under `evidence/`.
7. Independent review before publishing; fix factual/UI bugs with regression tests. Publish only site files with upload-html skill, return URL plus source/docs archive and paths. Clearly distinguish downloaded from installed/compiled/executed. No auto commits in downloaded upstream repositories.
