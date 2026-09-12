# Timing / VLIW / software-pipeline handoff

## Scope and reproduction

Only owned deliverables written: `wiki/content/spec-cycles.json`, `wiki/extract_schedule.py`, `wiki/spec-data/scheduling-model.json`, `tests/test_spec_schedule.py`, this note, and `evidence/spec/cycle-*.txt`. No build.py/content from another owner/assets/wiki-site/source snapshot edits; no packages, TableGen build, compiler execution, services, NPU, web, delegation, or publication.

Pin: llvm-aie `386ca5c6634a84bb224b7248e79df8edabf0722f`. Correct files are `llvm/lib/Target/AIE/aie2p/AIE2PSchedule.td` (AIE2P + Schedule) and `AIE2PGenSchedule.td`, **not** the `aie2ps` target. The extractor reads exact pinned Git objects via read-only `git show`, including files omitted by sparse checkout. Python dependencies are stdlib only; Git is the existing local source-object reader. It emits JSON to stdout and never writes sources.

```sh
python3 -B wiki/extract_schedule.py > wiki/spec-data/scheduling-model.json
python3 -B tests/test_spec_schedule.py
```

Parent integration: load the three articles using the existing content loader and copy/link `wiki/spec-data/scheduling-model.json` to the site's `spec-data/scheduling-model.json`. This worker intentionally did not modify build.py or build the site. Dataset is approximately 15 MiB because it intentionally retains raw definitions (including the large ProcessorItineraries container), precise per-record provenance, and parsed values; prefer a download link over inlining it in page HTML.

## Test-first evidence

- `evidence/spec/cycle-red.txt`: initial test run before extractor existed, exit 1.
- `evidence/spec/cycle-red-coverage.txt`: genuine intermediate failure, independent source inventory found **620 missing memory records**; article file was also still absent. An exact `InstrItinData` scanner incorrectly omitted `MemInstrItinData`. Coverage was fixed, not weakened.
- `evidence/spec/cycle-green.txt`: 10 tests pass, exit 0. Covers pin, deterministic checked-in JSON, full name coverage, hashes/ranges/raw slice equality, overlapping stages, empty-stage distinction, unrecognized complex raw retention, eWH bypass differences, memory points, model constants, formats, article schema/depth/citations/related links.
- `evidence/spec/cycle-source-ranges.txt`: SHA-256 and Git blob hash inventory, numbered immutable evidence URLs plus raw semantic implementation excerpts, actual itinerary samples, and distribution/count evidence.

## Exact counts and coverage

| Inventory | Count |
|---|---:|
| Model def/class records in the four scheduling files | 4,095 |
| InstrItinClass declarations | 4,013 |
| Generated itinerary records | 4,010 |
| Handwritten ExtraItineraries records | 3 |
| Total itinerary records | 4,013 |
| Ordinary InstrItinData, including 3 handwritten | 3,393 |
| MemInstrItinData | 620 |
| Literal parsed itineraries / raw-only itineraries at this pin | 4,013 / 0 |
| FuncUnit definitions, including two synthetic resources | 73 |
| Target bypass definitions (MV / VEC) | 2 |
| Composite format defs (76 generated + I16_NOP) | 77 |
| Hashed model / format / semantic source files | 24 |

Memory point list distributions: `[5]`: 534; `[7]`: 48; `[4]`: 12; `[5,11]`: 12; `[6]`: 7; `[8]`: 7. Format bit-width distribution: 16:1, 32:6, 48:10, 64:9, 80:21, 96:20, 112:8, 128:2.

Counts are **source-model records, not instruction counts**. Many register-specific move variants share operations. Every declaration has a data record in this bounded model inventory; this does not mean every possible opcode/lowering is modeled or experimentally validated. Raw-only itinerary count zero means literal fields fit this parser, not that all TableGen/target semantics have been evaluated. Complex generic classes/composite encoding expressions stay raw. Unsupported itinerary syntax is retained with an explicit parse note and null parsed payload, never guessed values.

## Granular source map (all paths under pinned llvm-aie)

Immutable prefix: `https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/`.

- `llvm/lib/Target/AIE/aie2p/AIE2PSchedule.td:11–32`: IssueWidth/MicroOpBufferSize 1000; LoadLatency 5, MispredictPenalty 4, HighLatency 37 all FIXME; CompleteModel 0.
- `aie2p/AIE2PGenSchedule.td:12–31`: EmptyCycles, PrefixCycle, SimpleCycle, 7-cycle PART_WORD_STORE Required vs weak Reserved.
- Same file `33–109`, `4223–4310`: FU/bypass declarations and ProcessorItineraries container; full generated data extends through `10075`, handwritten include at `10077`.
- Same file `4309–4325`: ABS empty stages and lock LCKREQ=4; `4428–4434`: ADD operand points 1.
- Same file `4608–4623`: scalar load and register variants, dst=7 vs MemoryCycles=[5]; `8407–8414`: vector load; `9538–9545`: vector store.
- Same file `7858–7863`: part-word store late source=7 and memory points [5,11]; `9024–9064`: VMAC; `9355–9395`: VMUL; `8248–8264`: conversion/nonlinearity; `10018–10072`: accumulator subtract, unpack, UPS.
- `aie2p/ExtraItineraries.td:10–34`, `ExtraItinDecls.td:10–25`: eWH no-bypass forms; `AIE2PGenInstrInfo.td:6234,6285,11838`: operand-class bindings for VCONV/VEXP2/VTANH.
- `llvm/include/llvm/Target/TargetItinerary.td:41–120`: stage/operand/bypass/uops contract; `AIETarget.td:22–47`: MemInstrItinData extension and first/last memory access.
- `llvm/utils/TableGen/SubtargetEmitter.cpp:355–432`: TimeInc normalization and omitted bypass zero padding, read only, not executed.
- `llvm/include/llvm/MC/MCInstrItineraries.h:169–262`: actual stage latency and forwarding query implementation.
- `llvm/lib/Target/AIE/AIEBaseInstrInfo.cpp:892–1024`: signed RAW/WAR/WAW, one-cycle bypass hook and unsigned cap; `1363–1432`: resolved register-class variant; `1082–1165`: conservative lock stall/resume and memory-ordering exceptions.
- `AIEHazardRecognizer.cpp:133–178`: conflict semantics and stage interpreter; `224–275`: default issue-limit 6; `575–626`: format, memory and stage checks; `714–778`: nonmonotone self-conflict and software horizon.
- `aie2p/AIE2PSlots.td:13–67`: slot widths; `AIE2PCompositeFormats.td:24–78,1141–1216`: sizes and all generated format defs; both manual Include files: NOP format / artificial slot.
- `aie2p/AIE2PInstrInfo.cpp:1079–1113`: AIE2P hazard hook and conservative DONE 6.
- `AIEPostPipeliner.cpp:232–251`: resource gate; `466–503`: recurrence traversal; `541–566`: heuristic limitations; `1602–1686`: trip count and software stage peeling; `1709–1756`: prologue/kernel/epilogue and trip count adjustment.

Full paths, exact per-record character offsets/line ranges, immutable URLs and raw slices reside in JSON. Eleven particularly important semantic ranges are also embedded as raw `semantic_evidence` records.

## Nuanced cycle pitfalls preserved in public articles

1. Stage starts are zero-based reservations; memory access points are one-based and scoreboard subtracts one. TimeInc is a start-to-start delta, not an added execution latency. PrefixCycle overlaps; EmptyCycles has zero resource duration.
2. Empty FU list is not a zero-cycle instruction. getStageLatency's comment mentions a one-cycle fallback, but the actual populated-itinerary/empty-stages branch returns initialized zero; use operand points/edges for dependencies.
3. AIE signed RAW is W−R+1−bypass. WAR has no +1 and applies reverse-bypass correction; WAW has +1. Unsigned wrapper clamps negative edges, signed wrapper preserves them. No single instruction-wide data-ready number is fabricated.
4. Register class affects timing. eWH removes selected MV forwarding, so a valid VEXP2→VCONV edge can change from model spacing 1 to 2. Operand comment labels are not an independent proof of def/use ordering.
5. MemInstrItinData's fourth argument is MemoryCycles, not bypass. RMW must preserve both memory points, and load memory point 5 is not destination write point 7. A register variant can omit late FU reservations without changing operand cycle 7.
6. Required/Reserved is not symmetric exclusivity: Reserved/Reserved alone does not conflict. FU symbols are not an undocumented silicon-stage taxonomy or physical-unit census.
7. IssueWidth and MicroOpBufferSize 1000 are scheduler controls. Default hazard issue-limit 6, legal slot unions, all-cycle resources and operand constraints remain distinct gates. Seven named useful slot kinds cannot all coexist in one bundle; 128-bit forms provide six ordinary slots or five with Lng replacing Alu+Mv.
8. RecMII uses edge latency, not producer write point. Worked integer VMAC recurrence: 6−4+1−1=2. Two accumulators may lower per-original-update recurrence bound, but a two-update super-iteration still consumes two vec issue cycles.
9. SelfMII implementation tracks the last conflicting II plus one, not first feasible II. Source example offsets {0,3,7}: II=5 works, II=7 conflicts, so conservative gate 8 can skip smaller feasible choices.
10. Software NStages is not silicon pipeline depth. Prologue/epilogue, minimum trip count, register liveness, spills and code size prevent II×N from being a universal loop cost. Numeric examples explicitly state consumer-tail and resource assumptions.
11. Lock 2/8, LCKREQ 4 and DONE 6 are conservative/control/reservation model values, not fixed real wait durations. Memory ordering, stream backpressure, lock availability and external data arrival are distinct from exposed-pipeline register dependence safety.

## Articles and honest gaps

Three articles: `instruction-cycles` (5 H2), `vliw-pipeline` (6 H2), `software-pipelining` (6 H2), each comfortably beyond 800 non-URL characters. Each has near-claim immutable citations, rich numeric tables/derivations, sources {label,url,note}, related isa/compute/mma/performance/compiler plus both peer slugs, and the dataset link. They follow hardware.json's article schema and existing 架構/程式設計 categories.

No TableGen expansion, full opcode-to-itinerary mapping (other worker's scope), assembled bundle validation, compiler-optimality proof, runtime measurement, silicon internal stage naming, inter-tile hop latency, clock-frequency assumption or benchmark guarantee. CompleteModel=0 / FIXME values are prominent, not hidden. Parent owns tile/interconnect and final integration; no route/topology catalog was added here.
