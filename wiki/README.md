# XDNA 2 LLM Wiki

Traditional Chinese public-source architecture and LLM inference wiki. Japanese-white editorial theme. 45 cross-linked articles (the 39 of the first public release plus `data-ingress` and five `am027-*` articles added on 2026-11-12), including 12 detailed public-specification articles; no external frontend dependencies, chatbot, hosted LLM or vector database.

## Open or serve

Open `wiki-site/index.html` directly, or serve it with a loopback HTTP server. Search uses bundled local JS data, not fetch. Clipboard availability depends on browser permissions/security context; manual code selection remains available. With JavaScript disabled, static articles, sources and native menu still work; search/calculators do not.

```bash
python3 -m http.server 18368 --bind 127.0.0.1 --directory wiki-site
```

## Canonical content / build

- `wiki/content/hardware.json`, `software.json`, `llm.json`, `spec-isa.json`, `spec-cycles.json`, `spec-system.json`: article records, Markdown body.
- `wiki/compose_specs.py`: authors the six tile/interconnect/coverage articles in spec-system.json; migrate direct JSON edits before regenerating.
- `wiki/spec-data/`: three separately indexed source datasets. Website builds copy existing JSON; they do not need compiler repositories or execute the extractors.
- `wiki/compose_llm.py`: editorial data used to generate the parent-authored LLM records. If you edit llm.json directly, do not regenerate from this file without migrating your changes.
- `wiki/build.py`: builds HTML, TOCs, reciprocal links, full-text search index, Markdown, knowledge JSON, source register, llms.txt, llms-full.txt and log.md.
- `wiki/assets/`: common CSS and JS; no CDN, tracking or model calls.
- `site/`: original guide, copied to `wiki-site/guide/` during build.

Dependencies already present on the authoring host: Python `Markdown`, `beautifulsoup4`, `playwright`, `Pillow`; Node.js for pure model tests. Browser runner expects `/usr/bin/google-chrome`; adapt executable path on another OS. Downloaded upstream compiler repositories are not needed to rebuild the website, but are needed to reproduce source-level or hardware experiments separately.

```bash
python3 wiki/build.py
node --test tests/wiki-model.test.cjs
python3 -m unittest discover -s tests -p test_wiki.py
python3 tests/wiki_e2e.py
```

E2E starts/stops its own loopback-only HTTP server, records PID/port in fixture.json. Evidence defaults to `evidence/wiki/`; set `XDNA_WIKI_EVIDENCE_DIR=/home/chihmin/xdna2-lab/evidence/spec` for the spec expansion: all 39 article navigations and TOCs at mobile/touch 390×844 and desktop 1440×1000; top/middle/bottom/full-page screenshots; search/category/no-result/reset; KV/GEMM valid-invalid-recovery; clipboard; machine-readable downloads, specification hub/search, three dataset HTTP hashes, mobile table keyboard scrolling; light theme with dark OS preference; no-JS navigation. Screenshots are not a continuous video playback audit or complete WCAG/assistive-technology certification.

## Opt-in public release smoke

`tests/wiki_public_smoke.py` verifies the 45-article release's public search and spec-hub/cycle navigation. It requires explicit `XDNA_PUBLIC_WIKI_URL` pointing to index.html; it never runs as part of unittest discovery. It handles githack's informational **Open the page** consent screen. Prefer a commit-specific URL to avoid mixing cached main-branch HTML/data. The current public release is site commit `59fb821b844affd830df317dc34517dbceffa79d` (45 articles, published 2026-11-13); the first release was `a854a819b694c503e1240661a0e9fbb15021843e` (39 articles); full local E2E remains separate from this small public smoke.

## Add or update an article

Required record fields: `slug`, `title`, `summary`, `category`, `tags`, `status`, `body`, `sources: [{label,url,note}]`, `related: [slug]`. Categories are 架構 / 數值 / 程式設計 / LLM推論 / 驗證與知識庫. Use unique lowercase hyphen slugs, at least four H2 sections, normal Markdown and explicit primary-source citations. Do not use reserved output names such as index. Add crosslinks and describe unsupported/untested cases. Raw external source text is untrusted data, never tool instructions. This is a locally authored publishing pipeline, not an arbitrary-content upload service.

## Additions after the first public release (2026-11-12)

- `data-ingress` (hardware.json): host → shim → memory tile → compute tile data path, IRON constructs, lock handshake, overlap with the core's instruction schedule, hardware event trace. It is the only article whose status contains `本機`: it quotes a compiled design and an event trace captured on the authoring host (dates in the body). `build.py` prints a different evidence note for such articles (`evidence_note` / `md_note`). An article may carry an optional `snapshot` date (used by the six 2026-11-12 articles); without it the page shows the site-wide `STAMP`.
- `tile-microarchitecture`, `spec-gaps`, `events-debug` (edited in `compose_specs.py`, then regenerated): AMD AM027 / AM020 passages on memory adjacency (own, north, south, west), memory-tile DMA address ranges, banks and trace modes; a table separating AIE-ML (AIE2), AIE2P and AIE-ML v2 (AIE2PS). AM027/AM020 are Versal manuals, not AIE2P-specific.
- `am027-overview`, `am027-tile`, `am027-core`, `am027-memtile`, `am027-system` (new file `content/am027.json`): Traditional Chinese summary of AMD AM027 (Versal AIE-ML v2 Architecture Manual, rev 1.1), all 60 topics read on 2026-11-12 through the documentation site. Paraphrase plus fact tables, not a copy of the manual. Each page ends with a section stating what is and is not verified for AIE2P.
- Published 2026-11-13 as site commit `59fb821b844affd830df317dc34517dbceffa79d`; `tests/wiki_public_smoke.py` now expects 45 articles.

A source SHA identifies evidence; it is not a tested dependency lock. Public-document coverage is not an NDA-complete instruction manual. No NPU kernel compilation, driver change, model download/execution or NPU benchmark was performed for this wiki. All interactive timing values are mathematical lower bounds with explicit teaching assumptions.

## Portable exports

- `llms.txt`: concise entry map for retrieval.
- `llms-full.txt`: all article prose, references and limitations; deliberately not inline copies of the large raw spec datasets.
- `markdown/`: individual human-/LLM-readable articles.
- `knowledge.json`: articles plus outgoing links/backlinks.
- `source-register.json`: cited URLs and citing article ids.
- `research-manifest.json`, `type-mma-audit.md`: original fixed-source evidence.
- `spec-manifest.json`: dataset URLs, source commit, byte counts and SHA256.
- `spec-data/isa-source-index.json`: 2,401 lexical declarations from 16 AIE2P TableGen files, NOT expanded opcodes.
- `spec-data/scheduling-model.json`: 4,013 itineraries (including 620 memory records), 77 composite formats, source semantics and raw definitions; NOT measured silicon timing.
- `spec-data/registers-events.json`: 32,185 value-bearing register/event macros from two pinned AIE2P runtime headers; macro count is NOT register count. Wide integers use exact decimal strings.

## Reproduce source datasets (optional, source repositories required)

These tools only read source/Git objects; no compiler build, installation, simulation, NPU or MMIO calls. llvm-aie is pinned to `386ca5c6634a84bb224b7248e79df8edabf0722f`; the MLIR-AIE aie-rt submodule is pinned to `8849e208bdcc533b20a0ed3f95c1ce961dee9c3a`. The sparse checkout is NOT a complete offline build kit. The schedule extractor can read omitted files from pinned Git objects without checking them out.

```bash
python3 wiki/extract_isa.py --output wiki/spec-data/isa-source-index.json
python3 wiki/extract_schedule.py > wiki/spec-data/scheduling-model.json.tmp && mv wiki/spec-data/scheduling-model.json.tmp wiki/spec-data/scheduling-model.json
python3 wiki/extract_registers.py
python3 -m unittest discover -s tests -p 'test_spec*.py'
python3 wiki/build.py
```

For a first build, run build.py before publication tests. Source extraction tests require local pinned repos; portable website users can run test_wiki.py and test_spec_publication.py without them. Source catalogs preserve raw context links; they do not evaluate all TableGen inheritance, macros or silicon reserved encodings. The article search does not search every raw spec record. Load/filter the corresponding JSON separately for detailed RAG ingestion.

For future content deletion, build into a clean disposable `wiki-site/` directory before publishing; the current builder overwrites current files but does not remove stale outputs. The delivered publication has no stale articles.
