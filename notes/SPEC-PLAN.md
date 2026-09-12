# XDNA2 public specification expansion

User request: 你可以幫我把ISA spec , cycle 數 VLIW pipeline microarchitecture . Tile architecture interconnect 所有的 spec 都整理進wiki LLM 嗎

Scope: deepen the existing Japanese-white static wiki and every LLM export. Enumerate public-source coverage and explicit gaps, not claim possession of all silicon/undocumented/NDA specs. No NPU execution, compiler build/install, service changes, new model weights, or modification of fixed source snapshots.

Plan / progress (no todo tool available):
- [x] Research public manuals vs AIE2P arch21 source; search ledger preserved, 188 citation ranges checked.
- [x] ISA: three articles, 2,401 lexical declarations across16 files; not expanded opcode counts.
- [x] Scheduling: three articles, 4,013 itineraries (620 memory), 77 formats; machine-readable source model with caveats.
- [x] Parent: six articles and32,185 runtime field/event macros; explicit bank/trace/unit discrepancies and unknowns.
- [x] Test-first integration, standalone datasets and manifest/notices linked into llms exports;39 article graph.
- [x] Independent review → bounded fix agent → independent PASS.42 Python+16 Node tests;39-page local mobile/desktop E2E;12 new-article sample grids and final state pixels inspected.
- [x] Stable Wiki published at commit a854a819b694c503e1240661a0e9fbb15021843e;13 raw published files equal; immutable release used for verified public39-article search/navigation smoke. Portable archive tracked in deliverables/xdna2-llm-wiki-specs.zip.

Boundaries: same-source/compiler/runtime evidence is not three independent silicon confirmations. AIE2P not AIE2PS; compiler IssueWidth/resources/latency not unconditional hardware retirement/TOPS. Reservation stage cycles, operand latency, reciprocal throughput, loop II, memory stalls, packet beats and wall time are distinct quantities. Unknown physical clock/FIFO depth/hop latency/errata remain explicitly unknown unless substantiated.
