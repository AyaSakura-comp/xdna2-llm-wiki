# Independent final specification review

## Verdict and scope

**FAIL pending B1 and B2 below.** Passing automated tests do not establish factual accuracy.

Read all twelve bodies in `wiki/content/spec-system.json` (six), `spec-isa.json` (three), and `spec-cycles.json` (three); all three extractor implementations; dataset records; `wiki/build.py` and its diff against `evidence/spec/build-before.py`; all four `tests/test_spec*.py`; and both `notes/spec-{isa,cycle}-audit.md` after they became available. Author notes were secondary handoff information, not evidence for the values. Actual pinned Git objects were the source evidence.

Only this report and `notes/spec-review.json` were written as deliverables. No production edits, build invocation, source modifications, web, hardware access, services, or delegation. Parent retains rebuild/source-byte/E2E/visual/public checks. Publication tests read the existing parent-generated output; this is not an independent rebuild or public-site verification.

## Blocking fixes

### B1: false Shim same-channel restriction

Location: `wiki/content/spec-system.json:187`, article `interconnect`, section `合法交叉連接不是 full crossbar 任意互接` (the JSON body is one physical line).

Exact substring replacement:

```text
OLD: Shim：方向bundle同向須同channel
NEW: Shim：West/North/East同向回接須同channel；South→South在channel範圍內可跨channel
```

Keep the following Trace sentence unchanged.

Evidence: `sources/mlir-aie`, commit `0ed8e7e477fd9094acee8dada7ab81604a7fb07a`, `lib/Dialect/AIE/IR/AIETargetModel.cpp`:

- 1075–1079 checks source/destination count bounds.
- 1119–1123 handles **FIFO and South** sources, permitting destinations including South with no channel equality test.
- 1124–1131 handles **West, North, East** sources; only this branch requires equal channels when source and destination bundles match.
- 1132–1136 supports the article's separate Trace restrictions.

Concrete counterexample: Shim source South 0 → destination South 1 is within source count 8/destination count 6 and returns true. The article's blanket directional rule incorrectly forbids it. This is a compiler-model fact, not an uncertainty that silicon caveats can excuse.

### B2: nonexistent citation endpoint

Locations: `wiki/content/spec-cycles.json:15` (body) and `:64` (sources entry).

```text
OLD: MCInstrItineraries.h#L169-L264
NEW: MCInstrItineraries.h#L169-L262
```

Pinned `llvm-aie` commit `386ca5c6634a84bb224b7248e79df8edabf0722f`, `llvm/include/llvm/MC/MCInstrItineraries.h`, has **262 lines**, ending with the include-guard `#endif`. Thus line 264 is not an exact source endpoint. The actual stage-latency discussion at 169–185 is correct.

Keep the extraction specification consistent at `wiki/extract_schedule.py:242`:

```python
# OLD
("llvm/include/llvm/MC/MCInstrItineraries.h", 169, 264),
# NEW
("llvm/include/llvm/MC/MCInstrItineraries.h", 169, 262),
```

The current generated semantic-evidence record already reports endpoint 262: Python slicing silently truncates the requested 264. Its emitted raw text/range is correct, so this correction should not itself change dataset bytes. The cycle author's audit note repeats `169–264` and should be aligned by its owner. This is an exact-provenance acceptance defect, not a wrong cycle number.

## Nonblocking improvements

1. `wiki/content/spec-system.json:356,390`: change `xaie2pgbl_reginit.c#L2474-L2536` to `#L2467-L2536`. The omitted `.MaxCounterVal = 2U` is line 2469. The article's 2/4/2/4 counts are **correct**. Pinned `driver/src/perfcnt/xaie_perfcnt.c:95–107` distinguishes `Counter` from `CounterVal` and uses `MaxCounterVal` as the number of counters when requesting all of them. A representative counter field is width 32 at `xaie2pgbl_params.h:2167`, not width 2 or 4.
2. Add article citation-bound checks to cycle/system tests, the Shim South counterexample to factual tests, and checked-in register JSON round-trip equality to register tests. Extend scheduling range tests to formats and semantic excerpts. Independent checks covered those omissions for this review.
3. Optional hardening: ISA file enumeration via `git ls-tree` can detect omitted sparse-worktree files directly. Bound-check requested evidence ranges before slicing. Current ISA scope and emitted dataset ranges passed independent checks; no missing current file or corrupt current raw record was found.
4. Renderer guards remain for trusted author Markdown, not an arbitrary-input sanitizer. Literal extractors are bounded pinned-source readers, not general C/TableGen frontends. No extra general-input guarantee is needed for acceptance.

## Tests actually executed

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_spec*.py' -v
node --test tests/model.test.cjs tests/wiki-model.test.cjs
```

- Python: **25/25 pass**, including two publication tests against existing output.
- Node: **16/16 pass**; pure model/search/calculator tests, no browser or hardware.
- The existing Python suite verifies ISA deterministic regeneration/pinning/raw slices, scheduling record-name coverage and memory itineraries, register extraction, and publication links/hashes. It does **not** catch B1/B2.
- Additional independent in-memory checks used `git show` and `git ls-tree`, not extractor output as the sole expected result. Two exploratory assertions initially stopped (one discovered B2; another needed the real `InstrStage<4,[LCKREQ]>` constructor added to the independent checker). The completed checker covers that constructor and passed; these exploratory stops are not production-test failures.

## Independent dataset verification

### ISA

- Pinned Git tree enumeration matched all **16** immediate `.td` inputs after the four documented scheduling exclusions; not merely a matching worktree glob.
- **2,401** declarations: class 167, def 2163, defm 59, defset 6, multiclass 6. Generated instruction source has 879 declarations. These are lexical declarations, not instantiated instructions.
- Checked source hashes and all 2,401 raw slices against pinned Git bytes; existing tests also verify line endpoints, IDs, and deterministic regeneration.
- Sampled actual declaration bodies for scalar ADD/immediate ADD, LDA_2D_s8, VADD_8, accumulator VADD, VEXP2, integer VMUL/VMAC, VecConf, MOV/stream/FIFO/cascade and pseudo families.
- Comments, strings, code literals and outer `let`/`foreach` limitations are disclosed; raw-only source structure is not misrepresented as evaluation.

### Registers/events

- Independently compared both full pinned headers with the **checked-in JSON**, including source hashes, ordered names, every expression, source-line slice, and every claimed integer value.
- `xaie2pgbl_params.h`: **31,647** records; `xaie_events_aie2p.h`: **538**; total **32,185**. No manual claim to have read every macro semantically.
- Verified 128-bit program mask remains decimal string `340282366920938463463374607431768211455`; program window `0x20000`; representative counter width 32; Shim Buffer_Length width 32; core MEMORY_STALL event 23.
- Current numeric expressions checked independently contain no leading-zero decimal/octal ambiguity. Nonliteral expressions are not evaluated. No hardware reads or writes.

### Scheduling/formats

- Checked all 24 source-file hashes against pinned Git objects. Existing tests compare model definitions/itineraries/declarations and raw offsets; independent checks additionally covered every format definition, composite format and semantic excerpt.
- **4,013** itinerary records/declarations, including **620** memory and three handwritten eWH variants; **4,095** model definitions; **73** FuncUnit definitions; two named target bypasses; **77** composite formats. Literal fields fit all current itineraries; this is not full TableGen evaluation.
- Independently recalculated every parsed stage's cycles, unit, TimeInc, reservation kind, start/end and reservation extent from the bounded raw constructor syntax. Covered 5,385 PrefixCycle, 5,309 SimpleCycle, 939 EmptyCycles, 606 AvoidPartWordStore, 12 IsPartWordStore and nine InstrStage occurrences.
- Independently parsed all 620 raw MemoryCycles lists and compared first/last values. No missing RMW second point.
- All **187** unique-per-article inline Git citation ranges were checked against **36** unique blobs; B2 was the single out-of-bounds range. Range existence is not claimed to prove every sentence; substantive source reading is summarized below.

## Concrete factual checks

- **Architecture:** read both version headers: arch21/AIE2P versus arch22/AIE2PS. AIE2P+Schedule filenames are not confused with aie2ps.
- **Registers:** source loops/lists support 32 GPR, 16 pair views, eight pointers and each dimension component, eight D and four DS groups, four S source-class members, 24 W halves/12 X/6 Y overlapping views, four Q masks, 20 BM/10 CM/5 DM accumulator views, restricted four-member BM subsets, E/EX/EY metadata containers and FIFO1076-name/1088-class distinction. Source class/spill width is not independently proven silicon active-bit width.
- **Encoding/immediates:** actual ADD field order gives `0x10461`; composite gives `0x10823098`; no assembled-byte/endian claim. Signed/scaled immediate bases support c7s −64..63, c10s_step64 −512..448, c6s_step4 −32..28, c19s_step64 −262144..262080. VecConf bits and `(2<<1)|(3<<3)|(1<<5)=0x3c` agree with source; INT4 wrapper explicitly unpacks before mul/mac.
- **VLIW:** actual slot widths 17/20/42/20/22/20/26; composite counts by bits are 16:1, 32:6, 48:10, 64:9, 80:21, 96:20, 112:8, 128:2. Six-slot and five-slot-LNG 128-bit forms each use 125 payload bits plus three structure bits. IssueWidth/MicroOpBufferSize 1000 are source scheduler controls; debug issue-limit default 6 is separate.
- **Timing:** read TargetItinerary, AIETarget, AIEBaseInstrInfo and hazard interpreter. RAW W−R+1−B, anti dependency reverse bypass without +1, WAW +1, and unsigned clamp match. VMAC 6−4+1−1=2; scalar LDA write 7 versus memory [5]; ST_s8 late read 7 versus memory [5,11]; eWH removes selected bypasses. Empty resource stages are not zero execution latency. Required/Reserved conflict distinctions match implementation.
- **II:** read actual PostPipeliner recurrence/resource code and nonmonotone self-conflict loop. Two-accumulator versus two-update super-iteration distinction and {0,3,7} modulo example are correct. Ideal N=4 timeline ends at 14, average 3.5 versus steady II=2, with explicit one-unit tail assumption.
- **Tile/SRAM:** NPU2 six rows/eight full-model columns; 16KiB program, 64KiB core data, 512KiB memory tile; address windows and internal=east/self match. Bus 256, cascade 512 and vector alignment 512 are distinct. Allocator division establishes 4/8 partitions, while event names establish 8/16 indices, not a proved physical pairing.
- **Routing:** checked full source/destination/mux tables. S/D direction, all tabulated counts, edge exclusions and compiler Shim Trace=1 versus runtime slave Trace=2 are correct. Only the prose Shim same-channel generalization is false (B1).
- **DMA:** actual core/mem/shim modules give channels per direction 2/6/2, BDs 16/48/16, dimensions 3/4/3, stride 0x20; local locks 16/64/16 versus memory DMA lock-ID space 192. Read west/self/east 0/64/128 mapping. Model field widths, BD parity split and burst sets 64/128/256/512 versus 4/8/16/32 match; unit caveat is warranted, not a claim of link width or cycles.
- **Events/counters:** checked core event IDs, DMA starvation/backpressure names, bank indices, trace configuration values, and counter-count semantics separately from register width.

## Static code/build review boundaries

The three tools use fixed local paths/pins and literal JSON output, no eval/network/hardware execution. ISA verifies worktree bytes against pinned objects; other extractors read Git objects directly. Scheduling literal parsing uses guarded constructors and numeric/list syntax, retains unsupported records raw, and guards helper definitions against source changes. Current parsed stage values were independently checked, not accepted solely because a parse-status label said literal.

The builder diff adds ordering, specification entry links, three fixed-name copied datasets, byte/hash manifest, and explicit llms index/disclosures. It intentionally does not inline large source datasets in article search or `llms-full.txt`; that is documented, not a completeness bug. Existing trusted-author Markdown checks are not represented as a general sanitizer. No changed execution surface or blocking security issue found within this scope.

No claim of exhaustive instruction semantics, TableGen expansion, all source-subtree byte checks, arbitrary-input parser robustness, runtime silicon validation, external-site revalidation, or final E2E/visual/public acceptance.

## Reviewed article/dataset fingerprints (SHA-256)

```text
18d194480fceb8dcd1fad599a74973201694e1559688d365f676ff32e5e15d8a  wiki/content/spec-system.json
cad3896e159b109a37f5c56d642278b661ac69790242c82540cc02f2955f6498  wiki/content/spec-isa.json
b7f43c06f4d59d1dd1965e7522872ff67d2ed610efa11ce22475250d4735d5ec  wiki/content/spec-cycles.json
169203924e3c74f0acdc508677c3bcbb53ab70bbc1a19c544a6f21eea2add3d0  wiki/spec-data/isa-source-index.json
9773c957aad6b0b4f621aa0a59f843c474b139f34fa29569690b0927d2997af5  wiki/spec-data/scheduling-model.json
81c1a6bf4703846c1ba88b45ed06194c1f4258d71a163aa120d6958c45e387f7  wiki/spec-data/registers-events.json
38c13c929a6ceb8aa04e6404afdd6efb716b921ce910088986d6b25340b29eaf  wiki/build.py
```
