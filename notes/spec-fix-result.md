# Bounded specification fix result

**PASS for the requested source/article fixes; publication rebuild remains with parent.**

## Changes

- `wiki/compose_specs.py`: replaced the blanket Shim directional restriction with `Shim：West/North/East同向回接須同channel；South→South在channel範圍內可跨channel`, adding a direct pinned `AIETargetModel.cpp#L1119-L1131` citation. Trace wording and existing channel-bound/routing caveats are unchanged.
- Same composer: expanded Runtime PerfMod citation to `#L2467-L2536`.
- Regenerated **only** `wiki/content/spec-system.json` using `python3 -B wiki/compose_specs.py`; its source list includes both citation changes.
- `wiki/extract_schedule.py`: semantic evidence tuple endpoint `264` → `262`.
- `notes/spec-cycle-audit.md`: corresponding endpoint `169–264` → `169–262`.
- Added `tests/test_spec_claims.py`: four narrow regressions for canonical/generated Shim wording and citation, pinned South branch/counterexample evidence, PerfMod span, and cycle endpoint consistency.
- Parent's `spec-cycles.json` already contains `#L169-L262` in body and source list. **Not edited or regenerated.** Parent's `tests/test_spec_citations.py` was not edited.

## Independent source confirmation

Read pinned local Git blobs, not merely the review assertions:

- mlir-aie `0ed8e7e477fd9094acee8dada7ab81604a7fb07a`, `lib/Dialect/AIE/IR/AIETargetModel.cpp`: upper channel-bound checks at 1075–1079; FIFO/South branch at 1119–1123 admits South without equality; West/North/East branch at 1124–1131 applies same-bundle channel equality. South source count is 8 (981–982), destination count 6 (908–909): South 0 → South 1 is an in-bounds cross-channel counterexample. Worktree bytes matched the pinned blob.
- aie-rt `8849e208bdcc533b20a0ed3f95c1ce961dee9c3a`, `driver/src/global/xaie2pgbl_reginit.c`: memory/core PerfMod declaration begins at 2467; memory `.MaxCounterVal = 2U` is at 2469.
- llvm-aie `386ca5c6634a84bb224b7248e79df8edabf0722f`, `llvm/include/llvm/MC/MCInstrItineraries.h`: exactly 262 lines.

These are source-text/model checks, not compiled C++ execution or hardware validation. Excerpts: `evidence/spec/fix-source.txt`.

## Verification

All Python commands used `PYTHONDONTWRITEBYTECODE=1` and `python3 -B`.

1. **Red before production edits:** `-m unittest discover -s tests -p test_spec_claims.py -k shim_statement -v` exited 1 with assertion failures for missing corrected canonical/generated wording and direct citation. Log: `evidence/spec/fix-red.txt`.
2. **Green:** `-m unittest discover -s tests -p test_spec_claims.py -v`: **4/4 pass**. Log: `evidence/spec/fix-green.txt`.
3. **Full spec suite:** `-m unittest discover -s tests -p 'test_spec*.py' -v`: **31/31 pass**, including parent's citation checks. Log: `evidence/spec/fix-all-tests.txt`.
4. Byte-level expected regeneration comparison passed: baseline plus only the requested Shim statement/direct citation/source entry and PerfMod body/source span changes equals regenerated JSON. All other article data/caveats preserved. Evidence: `evidence/spec/fix-system-before.txt`, `evidence/spec/fix-preservation.txt`, `evidence/spec/fix-regenerate.txt`.

No site build or publication regeneration was run; passing publication tests inspect existing output and do not prove it incorporates this fix. No toolchain, NPU, services, source snapshots, build.py, wiki-site, external web, or delegation changes/actions. Writes were confined to the owned fix files/evidence (existing tests use their own temporary output). Workspace root is not a Git repository, so preservation was checked against a captured pre-edit JSON baseline rather than a root Git diff.
