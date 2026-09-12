# Bounded wiki fix result

Read `notes/wiki-review.json` and `notes/wiki-code-review.json`. Fixed only the requested issues in the five owned source/content files; this note is the only additional authored file. Review reports and tests were not edited.

## Exact fixes

- `wiki/compose_llm.py`: replaced the false glossary VLIW dependency-stall claim with the factual review's precise distinction: AIE2P's exposed pipeline relies on compiler scheduling of instruction dependencies/register access timing, not ordinary instruction-dependency stall logic; lock/stream dataflow waits are separate. Added `peano` to the `S` map, an inline glossary citation, and glossary source refs targeting immutable `Xilinx/llvm-aie` commit `386ca5c6634a84bb224b7248e79df8edabf0722f`, `README.md#L29-L45`. Checked the local README and repository HEAD.
- `wiki/content/llm.json`: regenerated only via `python3 wiki/compose_llm.py` (12 parent-authored chapters); no other content generator ran.
- `wiki/assets/model.js`: GEMM rejects TOPS or bandwidth below 0.1, preserving the existing finite-input/maximum checks, and explicitly rejects non-finite derived compute/memory timings. Their maximum therefore also remains finite. Both 0.01 and 1e-320 throw; 0.1 is accepted.
- `wiki/build.py`: checked all existing rendered article-body tags, then replaced the dangerous-tag denylist with the requested Markdown tag allowlist. This rejects base/meta/link and the previously rejected dangerous tags before generated wrappers/buttons are inserted. Existing event-attribute and URI-scheme checks remain. This is still a trusted-author boundary, not a general-purpose attribute sanitizer.
- `wiki/assets/app.js`: copy success and failure both update `aria-label` to match the visible message. Optional search URL synchronization catches only `SecurityError` from `history.replaceState`; unrelated exceptions are rethrown.

## Validation

- `node --test tests/wiki-model.test.cjs`: **8/8 passed**, tests unchanged.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_wiki.py`: **6/6 passed**, including source regressions and functional checks against existing publication output.
- In-memory source rendering: all **27** article bodies pass the allowlist without calling `build()`.
- In-memory Node VM checks passed for search under a simulated history SecurityError, copy success/failure accessible names, and rethrow of unrelated history errors. No browser QA claimed.
- Before/after combined path/content SHA-256 checks were identical for `wiki-site` (78 files) and `tests` (12 files):
  - `wiki-site`: `d92066044ba2baede88d1d93d34ea40dffa7f2e49a62a59ba741e914f5ca84d6`
  - `tests`: `90f3e87ca56a077219f12e0adf2f046ca9289d99eee9a95b59da1faae9ac6b07`

**No wiki-site rebuild**, delegation, service interaction, NPU execution, or out-of-scope stale-output/fragment/reserved-slug changes. Existing publication intentionally remains unchanged for parent screenshot/review work; source fixes await the parent's rebuild.
