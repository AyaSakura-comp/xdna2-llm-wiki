# XDNA2 LLM Wiki research log

Research snapshot: 2026-09-12 Asia/Taipei. Existing source HEADs retained, not pulled or rebuilt. No NPU execution, weight downloads, service modifications or new compiler installations.

## Acquired / compared external sources
- https://github.com/amd/Triton-XDNA — experimental compiler; runtime ABI, shared-buffer and platform requirements. Main may change; production wiki cites existing SHA 5c33df1263f29de30f71616780c2e8a88e623782 source instead.
- https://github.com/amd/Triton-XDNA/tree/main/examples/qwen2_5/ — model routing table: NPU mode is CPU+NPU, not all operators NPU. Contradiction: old prose still says attention and LM head always GPU. Assigned source-level resolution to software author, not accepted blindly.
- https://amd.github.io/Triton-XDNA/ — checkmarks mean transform file availability, not benchmark/correctness certification. GPT2/Qwen examples and zero_copy discovered.
- https://www.amd.com/en/technologies/xdna.html — public spatial-dataflow background. XDNA overview clock claims not imported into fixed XDNA2 tile specs.
- https://gist.github.com/SVTA-OP/f55218287b4cc42b297cfdf44a993033 — third-party all-NPU/zero-CPU/BIOS tips not independently verified; not adopted as operating instructions or performance evidence.
- https://deepwiki.com/amd/Triton-XDNA — crawl failed circuit breaker; no facts inferred from inaccessible contents.
- https://github.com/ROCm/FastFlowLM — primary deployment alternative. Orchestration and CLI MIT, binary kernels separate terms; free usage != completely source-rebuildable kernels. Performance/256k claims are upstream claims, not local results.
- https://fastflowlm.com/docs/install_lin/ — runtime-specific Linux compatibility and validation process. Published date differs from announcement; no inferred release history. Driver compatibility requirements differ from IRON guide and cannot be flattened into universal requirements.
- https://lemonade-server.ai/flm_npu_linux.html — Linux deployment integration; warns kernel/firmware/driver/memlock runtime conditions. Not executed.
- https://arxiv.org/abs/2205.14135 — FlashAttention v2, IO-aware exact attention algorithm, GPU paper; not AIE2P implementation evidence.
- https://arxiv.org/abs/2305.13245 — GQA v3; distinguishes query vs KV head count.
- https://arxiv.org/abs/2306.00978 — AWQ v6; weight-only calibration/packing and hardware-aware implementation, not arbitrary XDNA native INT4.
- https://arxiv.org/abs/2309.06180 — PagedAttention v1; paging reduces cache management waste, not the payload bytes/token algebra.

## Source quality and scope
Search first used three Google directions with no results; DuckDuckGo discovery and batch primary-source crawl succeeded. Search result snippets were not used as proof. Image candidates were generic GitHub cards/badges and earlier-XDNA product stock images, not relevant XDNA2 technical diagrams; reused existing attributed technical figures instead.

Multiple same-vendor repos are not independent silicon validation. General math can be derived and checked with tests; architecture facts require pinned target/source evidence; performance requires measurements. Lack of public docs is recorded as a gap, not filled with invented ISA details.

## Second research loop / primary-source contradictions
FastFlowLM HEAD resolved to 089e56d29416990e168abed43aff88fc0ad664f3. README.md, TERMS.md and LICENSE_RUNTIME.txt downloaded with SHA256 into wiki/raw/. The same-SHA README says binary kernels are free for any use including commercial, while TERMS.md calls them proprietary and requires an explicit commercial license above USD 10 million company annual revenue. Wiki deployment/sources explicitly preserve this conflict; no unconditional commercial-use permission asserted.

Four versioned papers downloaded with SHA256; extracted text retained locally. FlashAttention v2 algorithm1 and tiling/online-softmax discussion read directly, along with GQA head-count and PagedAttention block-management discussion and AWQ calibration/packing passages. Paper algorithm reasoning is not a hardware mapping claim.

Independent factual review read all 27 records, cross-checked 101 pinned citation ranges across 64 files and found one residual glossary VLIW stall wording error. Corrected against Peano exposed-pipeline text; kept lock/stream waits distinct. Independent code review found tiny positive roofline inputs could overflow to Infinity; model limits now match UI min0.1. A fresh fix agent and independent final re-review completed; final blocker arrays empty.

## Wiki completion ledger
- [x] Main research and source contradictions identified.
- [x] Hardware and software source-authored chapters integrated (27 total).
- [x] Links, formulas, search, exports and responsive states verified; screenshots sampled top/middle/bottom on every page, no continuous video audit.
- [x] Independent review completed; publication tracked in notes/publish-wiki.log.
