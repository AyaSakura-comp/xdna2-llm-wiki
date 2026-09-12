# AIE2P public ISA source audit / parent handoff

## Deliverables and boundary

Owned work only: `wiki/content/spec-isa.json`, `wiki/extract_isa.py`, `wiki/spec-data/isa-source-index.json`, `tests/test_spec_isa.py`, this note, and `evidence/spec/isa-*.txt`. No build.py, published wiki-site, checkout, stylesheet, E2E, browser, install, compilation, publishing, or delegation changes. Articles use the existing `hardware.json` Markdown-body schema; Japanese-white presentation remains the parent's existing renderer responsibility.

Pinned repository: `https://github.com/Xilinx/llvm-aie`, commit **386ca5c6634a84bb224b7248e79df8edabf0722f**. Sources are the local sparse checkout `sources/llvm-aie`. Only **AIE2P arch 21**, never AIE2PS arch 22. `clang/lib/Headers/aie2p/aie2p_version.h:14–20` establishes the compiler target boundary, not silicon capabilities.

Three articles (category 架構, status 來源查核):

| slug | body Unicode characters | H2 sections | inline-linked source entries |
|---|---:|---:|---:|
| isa-registers | 7030 | 7 | 13 |
| isa-encoding | 8077 | 7 | 15 |
| isa-instructions | 13769 | 8 | 33 |

All required fields are present. Related links use only isa/compute/datatypes/mma and the three new peer slugs. All article sources use immutable commit + inclusive line ranges. All three bodies link `spec-data/isa-source-index.json`; parent must integrate/export it, not this worker.

## Reproduction and red → green evidence

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_spec_isa.py -v
python3 wiki/extract_isa.py --output wiki/spec-data/isa-source-index.json
# Optional explicit checkout path:
python3 wiki/extract_isa.py --source-root sources/llvm-aie --output /tmp/isa-source-index.json
```

Tests were written **before** the extractor. `isa-tests-red.txt` retains the initial unavailable `python` invocation (127), followed by an actual `python3` test run failing because `wiki/extract_isa.py` did not exist. That setup error is the initial contractual red, not a claimed execution of five passing/failing test bodies. `isa-tests-intermediate.txt` then shows the extractor tests passing while the articles were still absent.

A further test-first regression (`isa-tests-defset-red.txt`) caught `defset list<Foo> Group` incorrectly reporting `list` instead of `Group`; the extractor was corrected afterwards. `isa-tests-citation-red.txt` retains the article source-range failure for a shared file ending at line 39 rather than 41. Final **9 tests pass**, exit 0: `isa-tests-green.txt`.

Checks cover lexical comment/string/code-block masking, nested/anonymous and defm/defset names, balanced source slices, rejection of unclosed definitions, exact file scope and counts, every raw slice and line range, source SHA-256, exact immutable URLs, unique offset IDs, deterministic JSON regeneration, unchanged source hashes after CLI execution, rejection of wrong commits/modified inputs, and refusal to place output inside the source tree. Article schema, length, headings, tables, links and source-range bounds are checked. Static ADD bit arithmetic and BF16 control-word arithmetic are also tested; these are NOT assembler/disassembler tests.

`isa-source-verification.txt` independently compares **20 unique catalog/article-cited source files** byte-for-byte with `git show COMMIT:path`, recording their SHA-256 hashes. Sixteen are catalog inputs; the four extra cited sources are two shared AIE base files, the architecture version header and the C vmult helper header. No claim that unrelated checkout files or other workers' work were checked.

Final catalog SHA-256: `169203924e3c74f0acdc508677c3bcbb53ab70bbc1a19c544a6f21eea2add3d0`.

## Exact extraction scope and counts

Scan **all immediate `llvm/lib/Target/AIE/aie2p/*.td`**, excluding exactly `AIE2PGenSchedule.td`, `AIE2PSchedule.td`, `ExtraItinDecls.td`, `ExtraItineraries.td`. This intentionally includes supporting calling convention, copy materialization, register-bank and instruction-pattern declarations instead of silently claiming only encodable instruction forms were counted.

**16 files, 2401 source declaration records:** class=167, def=2163, defm=59, defset=6, multiclass=6, defvar=0. Nested declarations are counted independently; parent raw bodies can overlap their children's raw bodies.

All paths below have prefix `llvm/lib/Target/AIE/aie2p/`; source coverage is the complete line range `1–last line` for each file:

| file | declarations | last line |
|---|---:|---:|
| AIE2P.td | 8 | 70 |
| AIE2PCallingConv.td | 19 | 230 |
| AIE2PCompositeFormats.td | 160 | 1216 |
| AIE2PCompositeFormatsInclude.td | 3 | 29 |
| AIE2PCopyMaterialization.td | 47 | 116 |
| AIE2PGenInstrInfo.td | 879 | 11975 |
| AIE2PImmOperands.td | 41 | 72 |
| AIE2PInstrFormats.td | 4 | 43 |
| AIE2PInstrInfo.td | 58 | 332 |
| AIE2PInstrPatterns.td | 491 | 1633 |
| AIE2PMultiSlotPseudoInstrInfo.td | 50 | 394 |
| AIE2PRegOperandDef.td | 58 | 69 |
| AIE2PRegisterBanks.td | 3 | 17 |
| AIE2PRegisterInfo.td | 563 | 1011 |
| AIE2PSlotInclude.td | 1 | 26 |
| AIE2PSlots.td | 16 | 113 |

The generated-instruction file contains 879 literal def declarations and 338 distinct literal mnemonic strings in an auxiliary exploratory scan (`isa-selected-definitions.txt`), **not** 338 complete semantic operations or 879 silicon opcodes. CompositeFormats has 84 classes/76 defs; CompositeFormatsInclude adds 2 classes/1 def. No inference from these counts to silicon decode-space completeness.

## JSON schema v1

Root fields:

- `schema_version`: integer 1.
- `source_repository`, `source_commit`, `architecture`, `scope`: identity and explicit limitations.
- `excluded_files`: exact scheduling/itinerary exclusions.
- `counts`: files, records, and by_kind (only occurring kinds appear).
- `files[]`: `source_path`, `sha256` (exact file bytes), `git_blob_sha1` (Git blob header plus bytes), `byte_count`, `line_count`, `record_count`, whole-file `source_url`, literal `includes[]` (not resolved/evaluated).
- `records[]`: `id` = path + colon + character start offset; `source_path`; `kind`; `name` (raw unevaluated name expression, null for anonymous declarations); `line_start`/`line_end` (1-based inclusive); `offset_start`/`offset_end` (0-based **Unicode character** offsets, end-exclusive); `raw_text`; immutable `source_url`.

`source_commit` applies to every file/record. Hashes are attached once per file, not redundantly per declaration. Sorted paths, lexical record order, deterministic counts/indentation and no runtime timestamp make the output byte-reproducible. The extractor checks HEAD and every selected source against the commit's Git blob before output. It only reads the checkout; its only intended write is the requested output outside the source tree.

Algorithm: regex-mask comments, quoted strings and TableGen `[{...}]` code literals while preserving offsets/newlines; discover declaration keywords; find the balanced body or top-level terminating semicolon with template/parenthesis/list tracking. Preserve original unmasked raw slices. It is a deliberately small, pinned-input lexical scanner, **not a general TableGen parser**. Type/header syntax outside this checked source revision is not promised.

**SOURCE DEFINITION scope:** regex-source records are **not fully instantiated TableGen opcodes, aliases, expanded multiclasses, or a silicon complete ISA**. Outer `let`/`foreach` context is not included in raw def slices, nor is inheritance, predicate selection, include expansion or alias resolution evaluated. Use the full-file immutable link/context for inherited flags, register expansion and side effects. All declarations are inventoried, but source statements such as `let`, `foreach`, `include`, and individual field assignments are not independent declaration records. `defvar` is supported but absent in the selected sources.

## Source-grounded findings and representative ranges

- RegisterInfo 82–238: GPR encoding width 5 versus value width 32; 32 GPR names, 16 pair views; 20-bit address values with 32-bit spills; 80/160-bit dimension objects with 128/256-bit spills. Pair comment says starting R16, but loop and eL membership actually include r0 onward; articles explicitly prefer definitions.
- RegisterInfo 403–469, 603–698: 20 BM512/10 CM1024/5 DM2048 overlapping accumulator views; 24 W256 halves/12 X512/6 Y1024 overlapping vector views; 4 Q128 masks with synthetic QL/QH. Counts are **manual interpretation of explicit lists/loops**, not extractor expansion or register-allocation availability.
- RegisterInfo 700–900: QX640/QY1280, E64, EX576/EY1152, QEX704/QEY1408 combine data and metadata. These do not prove native FP8 or IEEE FP16 arithmetic.
- RegisterInfo 240–400, 902–977: control/status/singleton/FIFO state; class-specific operand encoder caveat. The class named Vector1076Fifo actually configures 1088 bits; subfields total 1076. Do not publish either as independently measured hardware FIFO width.
- Slots 13–113; CompositeFormats 12–204, 1109–1216; CompositeFormatsInclude 11–29: widths 16/32/48/64/80/96/112/128; payload LDB17/ALU20/LNG42/LDA20/MV22/ST20/VEC26, NOP1. LNG replaces ALU+MV in the demonstrated wide formats; not seven unrestricted simultaneous functional units.
- GenInstrInfo 183–201 plus CompositeFormats 106–117: derived `add r1,r2,r3` ALU payload 0x10461, independent 32-bit Inst 0x10823098. This is bit concatenation, not assembled bytes or endian verification.
- ImmOperands 12–70 and AIEBaseInstrInfo 34–159: signed/unsigned and scaled operands, including c7s, c10s_step64, c19s_step64 and negative spill forms.
- GenInstrInfo 493–562, 6769–8692, 10246–11049: scalar/vector load-store, signedness and tied address outputs, 2D/3D, unpack/UPS/SRS/pack, FIFO forms.
- GenInstrInfo 5899–6022: VADD_8/16/32 are **MV-slot**, whereas accumulator VADD is VEC-slot; SIMD and slot names must not be conflated.
- GenInstrInfo 432–491, 4083–4146, 4245–4420, 9131–9437: control flow, lock/release, stream/TLAST/status, cascade. No waits, throughput or timing claims.
- GenInstrInfo 8763–8930, 9606–9758 and InstrPatterns 261–329: integer/BF/BFP VMUL/VMAC, explicit accumulator/control operands and compiler selection, not arbitrary C mmul shapes as single opcodes.
- InstrPatterns 30–70 and clang vmult.h 15–37: 32-bit VecConf map; signY bit8/signX bit9, mode combination and BF control word 0x3c. `amode=FP32` describes accumulator mode, not evidence for FP32 inputs.
- clang vmult.h 39416–39447: a specific INT4 wrapper performs shuffle/extract/unpack then mul/mac; bounds that wrapper claim without asserting all low-bit modes absent.
- InstrInfo 26–146, MultiSlotPseudoInstrInfo 11–57, InstrFormats 14–43: pre-scheduling, meta, split and multislot pseudos versus compiler-only but encoded MOV_OR.

Every article has inline citations near claims and a matching immutable source list. Full exact ranges are in those lists; auxiliary family-location evidence is navigational, not a semantic emulator.

## Unresolved gaps and deliberate omissions

1. No complete TableGen expansion, aliases/multiclass expansion, instantiated register universe, reserved-register/ABI allocatable inventory or silicon exhaustive ISA. The catalog's definition counts must retain their qualifier in parent integration.
2. No complete C/API function catalog. Only small C/header excerpts clarify architecture identity and show wrapper lowering boundaries. Shared base .td files are cited/hashed where needed but not recursively inventoried; other AIE targets are not cataloged.
3. No detailed cycle/itinerary timings, pipeline bypass analysis, fixed clocks, throughput/TOPS, latency, DMA throughput, or actual performance. Four scheduling files deliberately excluded; itinerary identifiers may still occur in raw instruction definitions and are not interpreted.
4. No general emitter/disassembler/relocation C++ audit, endian dump validation, all don't-care assignments, every bundle legality rule or hardware execution test. Register operand wrappers can require specialized encoders; only direct GPR bit arithmetic is worked through numerically.
5. Matrix lane/layout/legal-mode semantics and numerical error/exception behavior remain partial. No fabricated native FP8/IEEE FP16/INT4 claim; no assertion that an enum name or accepted C dtype proves native execution. BF16/BFP and FP32 accumulators remain distinct.
6. No site build/publish/E2E: parent must merge the three articles into its content-loading/export flow and export `spec-data/isa-source-index.json`. Existing theme/rendering is deliberately untouched.
