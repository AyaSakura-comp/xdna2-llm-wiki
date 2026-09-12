# Public ISA / cycle / microarchitecture expansion — research ledger

Clock anchored by gettime 2026-09-12 14:56:32 +0800 CST. User requested every spec integrated into the existing LLM Wiki, including ISA, cycle counts, VLIW pipeline microarchitecture, tile and interconnect. No claim of access to a complete NDA silicon manual.

## Search and crawl pass
Google parallel directions: XDNA2/AIE2P primary architecture/ISA; official AM020/AM027 identity boundary; open source DMA/stream/bank details. Retrieved results (all discovery URLs retained):
- https://github.com/amd/xdna-driver/blob/main/src/driver/doc/amdnpu.rst — crawled, 404 at current branch; not cited as working documentation.
- https://docs.amd.com/r/en-US/am027-versal-aie-ml-v2/AIE-ML-v2-Memory-Tile-Locks-Module-and-Stream-Switch?contentId=Dnu6GSg0nTvfoaarNlVLtg — search only, Versal manual not AIE2P evidence.
- https://github.com/joshmorgan1000/xdna-npu — crawled; community discovery, not authoritative numeric evidence.
- https://amd.com/en/technologies/xdna.html — crawled; generic XDNA page mixes original-generation discussion, including >1.3GHz. Not used as XDNA2 SKU clock proof.
- https://docs.amd.com/r/en-US/am020-versal-aie-ml/AIE-ML-Memory-Tile-Locks-Module-and-Stream-Switch — crawled loading shell only; not a full downloaded manual.
- https://github.com/Xilinx/mlir-aie/discussions/3390 — search only; not numeric evidence.
- https://destevez.net/2026/05/getting-peak-tops-on-a-ryzen-ai-7-350-npu/ — crawled; read architecture identity correction, exposed-pipeline and assembly example sections. Author explicitly corrected AIE2P vs AIE2PS and accumulator count; later prose still mixes AIE-MLv2 details. Use as external assembly-reading case, not Strix Halo 1.8GHz/pipeline/TOPS proof.
- https://docs.amd.com/r/en-US/am027-versal-aie-ml-v2/AIE-ML-v2-Architecture — crawled loading shell only. Kept in gaps, not silicon-derived numbers.
- https://ryzenai.docs.amd.com/_/downloads/en/1.3/pdf — search only; framework software manual, no additional ISA evidence.
- https://researchgate.net/publication/382164071_AMD_XDNA_NPU_in_Ryzen_AI_Processors — search only; did not use snippet date as publication fact.

Relevant external assembly image fetched: https://destevez.net/wp-content/uploads/2026/05/main_asm.png ; represents the author's external example, not locally generated assembly or NPU measurement. Other AMD marketing/product/gallery/Versal images were irrelevant or low-confidence for same-target microarchitecture.

## Primary-source work and second loop
- ISA worker read pinned llvm-aie TableGen register/encoding/pattern/instruction definitions, authored 3 chapters and reproducible literal source catalog. See spec-isa-audit.md.
- Timing worker traced BOTH InstrItinData and MemInstrItinData, generic LLVM field semantics and AIE operand-latency hooks/hazard recognizer/post-RA pipeliner. 4,013 records include 620 memory records; 77 composite formats. See spec-cycle-audit.md. Model fields IssueWidth=1000, LoadLatency=5, MispredictPenalty=4, HighLatency=37 must not become physical hardware claims.
- Parent read AIETargetModel NPU2 inheritance, complete source/destination/routing logic, memory and lock adjacency, allocator and AIE2P runtime reginit/params/events.
- Bank discrepancy prompted recursive dive: model getNumBanks core/mem=4/8; allocator divides SRAM into 16/64KiB regions. Runtime conflict event names expose indexes0..7 and0..15. No assumed physical pair mapping.
- Shim Trace discrepancy: compiler source count1 vs runtime NumPorts2. Preserved conflict, no invented availability.
- Mem DMA NumLocks192 vs local LockMod64: local neighbour index windows0/64/128 explain addressability, not 3x local lock storage.
- Compiler burst table64/128/256/512 vs runtime BurstLen4/8/16/32: kept as separate interfaces; ratio16 alone is not bus-width proof. Exact caller conversion remains a gap.
- Core SRAM MMIO program window0x20000 vs local program address0: different address spaces, not contradiction.
- Runtime register/event headers extracted as all prefixed value macros (32,185), not register count. Provenance read from exact pinned Git objects, not mutable worktree. Decimal strings preserve128-bit masks; no eval or MMIO.

## Evidence and scope
Three related software contracts (LLVM/MLIR-AIE/AIE-RT), not three independent silicon measurements. No toolchain installation/compilation, NPU execution, benchmarks, services, driver/kernel/ROCm changes or model downloads. Existing fixed source snapshots unchanged. Data sizes are intentionally separate from normal article search and full prose export; llms.txt plus spec-manifest.json index raw records for retrieval.
