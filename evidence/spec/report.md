# Public XDNA2 specification expansion — final verification

Published commit: a854a819b694c503e1240661a0e9fbb15021843e in AyaSakura-comp/TempHtml.
Immutable spec hub: https://raw.githack.com/AyaSakura-comp/TempHtml/a854a819b694c503e1240661a0e9fbb15021843e/xdna2-llm-wiki/spec-index.html
Stable destination also updated: https://raw.githack.com/AyaSakura-comp/TempHtml/main/xdna2-llm-wiki/index.html

## Scope delivered
Added 12 articles; now 39 total and 245 distinct cited URLs. New content includes AIE2P register aliases/classes/operand widths, bit/slot/composite encoding and worked ADD calculation, instruction families/control word/matrix distinctions, per-itinerary operand/resource/memory/bypass timing, VLIW constraints and exposed pipeline, software-pipelining/II arithmetic, tile SRAM/address/bank distinctions, full model switch port counts/routing, DMA/BD/lock/register fields, event/counter observation and explicit unresolved spec gaps.

Raw datasets: 2,401 source declarations from16 ISA files; 4,013 itineraries including620 memory records,73 model FU definitions and77 composite formats; 32,185 runtime register/event macros from two headers. None of these counts is misrepresented as a silicon instruction/register total. Large JSON stays separate from article full-text/search and is linked in llms.txt with a SHA256/size manifest. Upstream LLVM/AIE-RT license texts retained in spec-NOTICES.txt. No code/toolchain/NPU build or execution, drivers/services/ROCm changes, model download or hardware benchmarks.

## Research and independent review
Discovery and rejected/mixed-generation sources: notes/spec-research-log.md. Fixed-source author audits: notes/spec-isa-audit.md and spec-cycle-audit.md. Independent reviewer read all12 new article bodies and actual compiler/runtime sources; checked all2,401 ISA raw slices, all32,185 register expressions/value/ranges, all620 memory timing lists and every parsed stage's arithmetic. Reviewer separately checked actual register/bundle/latency/II/tile/routing/DMA/counter numbers, not just tests.

Initial FAIL correctly found one false Shim same-direction generalization (South can crosschannels; West/North/East same-bundle requires equal channels), plus a citation requesting line264 in a262-line file. Fresh fix agent corrected canonical content and source metadata; PerfMod citation also widened to include the memory counter-count line. Parent added source-range regression, new search-data content query for stable-publication cache identity, and upstream notice retention. Final independent re-review notes/spec-final-review.json PASS with empty blocking security/logic/factual arrays. Optional parser/cache hardening remains documented, not silenced.

## Automated results
- 42 Python tests passed; 16 Node pure model tests passed.
- Narrow Python AST execution-surface/syntax scan passed; not a general security certification.
- 188 new-article pinned citation ranges across36 blobs valid; range validity alone is not semantic accuracy.
- All39 canonical article records match knowledge.json; independent review checked article renderer and Markdown/full-text equivalence. All3 raw datasets byte-match copied output and manifest;107 publication files hashed.
- Complete maintained local E2E rerun after final fixes: 390×844 mobile/touch and1440×1000 desktop; all39 sidebar article destinations and every article's first TOC anchor; search/category/empty/reset; related navigation; KV/GEMM input/error/recovery including tiny positive model limits; actual clipboard;4 downloaded exports; spec-hub/cycle navigation and6/39 VLIW search;3 dataset HTTP hashes; mobile table keyboard internal scrolling; skip-link focus; OS-dark/light override and no-JS navigation. No unexpected page/console errors or document horizontal overflow. Primary controls>=44px; inline citations explicitly exempt.
- The E2E metric's legacy label 'all TOCs' means the TOC component of every article was exercised, not that every individual TOC link was clicked. Static tests check all internal fragments.

## Direct visual inspection
Read eight sample grids covering top/middle/bottom of each of12 new articles at both viewports, plus actual full-size cycle table, spec search, mobile internal table scroll, final corrected interconnect screenshots and spec hub. Final public mobile search/cycle screenshots also directly inspected. Japanese-white theme, table/code containment, source/backlink layout and focus remain coherent. Existing27 article bodies unchanged; automated navigation/overflow gates cover them with expanded navigation. No claim of every-pixel, continuous video playback, full WCAG or complete assistive-technology certification. Expected amber evidence/validation notes are intentional, not app failures.

## Public verification and encountered limitations
13 published raw GitHub files byte-match reviewed output, including all3 large datasets, notices, full text, knowledge, index and corrected cycle/interconnect pages. Public browser tool opened new hub, clicked its coverage TOC and Cycle link. Stable-main homepage showed old-looking search results; a subsequent browser-tool text request and reopen failed with ConnectionClosedError. No browser/service repair or restart was attempted. A raw urllib CDN probe received403, so it did not establish CDN byte equality.

Delivery therefore uses a commit-specific URL (all relative assets stay on the same immutable revision), verified with a small opted-in isolated Playwright public smoke. First attempt correctly stopped on githack's informational 'One more step' interstitial, not application content; after explicit 'Open the page', public smoke passed:39 visible articles, VLIW pipeline search6/39, spec hub navigation and cycle article, no page errors. Screenshots public-immutable.png/public-cycle.png show actual deployed output. This is not full deployed E2E, and content query alone is not claimed to purge cached HTML or control CDN query-key policy. Users may need to select Open the page once.

## Cleanup and portable export
Local E2E server PID/port recorded in fixture.json; server.shutdown/close and thread join in finally. Public smoke browser closed in finally; no unrelated services touched. Portable export contains published site, original guide source, canonical article records, three datasets, authors/build/extractors, tests, notices and reports; not full upstream Git objects, compiler toolchain or research PDFs. Rebuilding the site needs pre-generated datasets only; reproducing extraction requires the pinned source repositories.
