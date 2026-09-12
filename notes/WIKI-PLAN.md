# XDNA2 LLM Wiki Implementation Plan

**Goal:** Expand the existing Japanese-white XDNA2 guide into a linked, source-grounded Traditional Chinese architecture + LLM inference wiki, usable by people and LLM retrieval.
**Architecture:** Preserve `site/` as the original guide. Build `wiki-site/` from `wiki/content/*.json` article records using `wiki/build.py`. Markdown body is the canonical prose; build semantic static HTML, source references, related links, backlinks, JSON search index, Markdown per article, llms.txt and llms-full.txt. No chatbot/backend or NPU execution required.
**Stack:** Python markdown + BeautifulSoup (already installed), vanilla browser CSS/JS, Node unit tests, Python/Playwright acceptance.

## Contract
27 article slugs: system, compute, memory, dma, synchronization, isa, datatypes, mma, compiler, iron, triton, runtime, llm-graph, qwen-case, debug, gemm, attention, kv-cache, quantization, prefill-decode, heterogeneous, deployment, performance, validation, glossary, sources, wiki-method.
Article JSON: slug/title/summary/category/tags/status/body (Markdown)/sources [{label,url,note}]/related [slug]. Allowed categories: 架構, 數值, 程式設計, LLM推論, 驗證與知識庫. status marks source-inspected vs engineering derivation; no unexecuted experiment may be marked measured.

## Tasks
1. Research branch + log: verify missing LLM/runtime source details at fixed source commits; compare live upstream with frozen tree. Preserve sources/ unchanged. Record source contradictions and failed sources.
2. Parallel bounded authoring: hardware author -> wiki/content/hardware.json (8 pages); compiler/LLM case author -> software.json (7 pages). Parent -> llm.json (12 pages, including deployment license boundaries). Authors own disjoint files; no source edits or services.
3. TDD model: add tests/wiki-model.test.cjs for multiword/case-insensitive search and filter, KV payload formula, parameter payload, GEMM arithmetic-intensity/roofline lower bounds, invalid inputs. Run RED; implement wiki/assets/model.js; run GREEN.
4. TDD build contract: tests/test_wiki.py checks page count, unique slug/headings, related/backlinks, valid local anchors/assets, Markdown/LLM exports and absence of raw unescaped scripts in authored text. Run RED before wiki/build.py. Builder writes only wiki-site/; include original site under guide/ and source audit/manifest as evidence.
5. White editorial interface: sidebar navigation with mobile native details control, local full-text search + category filter and reset/no-results states, page TOC, related/backlinks, evidence badges, breadcrumbs, accessible cards, labeled diagrams. Normal links work without JS. KV/GEMM calculator embedded in relevant articles; explicit assumptions, no fabricated speed prediction.
6. Integration verification: all unit/build tests; maintained tests/wiki_e2e.py exercises every page and all interactive states at 390×844 and 1440×1000, direct screenshot/contact-sheet inspection, error/overflow/keyboard checks. No full video review claim because video inspection tool is unavailable.
7. Independent content/code review, resolve blockers. Package Markdown/HTML/wiki maintenance files; publish wiki-site only with upload-html; verify deployed artifacts match reviewed local bytes. Return wiki URL and portable source export.

## Boundaries
Public-document completeness is not full NDA ISA/SoC disclosure. No fixed clock, bus width, instruction latency or all-model NPU coverage without primary evidence. XDNA2 AIE2P arch21 != AIE2PS arch22. NPU mode may still execute CPU ops/fallbacks. LLM memory formulas are ideal payloads and theoretical lower bounds, never measured throughput.
