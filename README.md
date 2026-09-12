# XDNA 2 LLM Wiki

繁體中文、日系白底的 XDNA 2／AIE2P（arch21）LLM 技術 Wiki。涵蓋 ISA、register aliases、instruction encoding、compiler itinerary cycles、VLIW exposed pipeline、software pipelining、tile memory、interconnect、DMA／MMIO、事件除錯，以及 Transformer／GEMM／attention／KV cache／量化／異質部署。

- **39 篇文章**，245 個 distinct cited URLs
- **2,401** 筆 ISA 原始碼宣告（不是展開後 opcode 數）
- **4,013** 筆 compiler itineraries，含 620 筆 memory records、77 種 composite formats
- **32,185** 筆 runtime register／event macros（不是實體 register 數）
- 純靜態 HTML/CSS/JS，無 CDN、analytics、外部模型呼叫

## 線上閱讀

- [Wiki 首頁](https://raw.githack.com/AyaSakura-comp/TempHtml/main/xdna2-llm-wiki/index.html)
- [規格總索引](https://raw.githack.com/AyaSakura-comp/TempHtml/main/xdna2-llm-wiki/spec-index.html)
- [固定驗證版本](https://raw.githack.com/AyaSakura-comp/TempHtml/a854a819b694c503e1240661a0e9fbb15021843e/xdna2-llm-wiki/spec-index.html)

首次透過 raw.githack 開啟時，可能需要按一次 **Open the page**。

## Repository 結構

- `wiki/content/`：39 篇 canonical article records
- `wiki/build.py`：靜態網站、Markdown、搜尋索引及 LLM exports 產生器
- `wiki/compose_*.py`：內容編排來源
- `wiki/extract_*.py`：read-only pinned-source extractors
- `wiki/spec-data/`：完整 ISA／scheduling／register-event JSON datasets
- `wiki-site/`：可直接離線開啟及部署的成品
- `site/`：原始單頁 XDNA2 技術指南
- `tests/`：model、publication、source extraction 與 Playwright E2E tests
- `notes/`、`evidence/spec/`：來源 audit、獨立 review 與發布驗證摘要

`llms-full.txt` 只收錄文章正文；大型規格資料集由 `llms.txt` 與 `spec-manifest.json` 分開索引。上游授權全文保留於 `wiki/spec-NOTICES.txt`。

## Clone

兩個大型上游專案以固定 commit 的 Git submodules 表示：

```bash
git clone --recurse-submodules https://github.com/AyaSakura-comp/xdna2-llm-wiki.git
cd xdna2-llm-wiki
# mlir-aie 的 aie-rt nested submodule 供 register/event source tests 使用
git submodule update --init --recursive
```

LLVM-AIE commit：`386ca5c6634a84bb224b7248e79df8edabf0722f`  
MLIR-AIE commit：`0ed8e7e477fd9094acee8dada7ab81604a7fb07a`  
AIE-RT evidence commit：`8849e208bdcc533b20a0ed3f95c1ce961dee9c3a`

不下載 submodules 也能使用既有 datasets、重建網站及離線閱讀；需要重跑 source-extraction tests 時才需 materialize pinned sources。

## Build 與測試

```bash
python3 wiki/build.py
node --test tests/wiki-model.test.cjs
python3 -m unittest discover -s tests
python3 tests/wiki_e2e.py
```

完整 E2E 需要 Python Playwright 與 Chrome。`wiki/README.md` 說明 article schema、輸出清理及 opt-in public smoke。

## 證據界線

AIE2P／arch21 不等於 AIE2PS／arch22。Compiler scheduling model 不是 silicon 實測：文章中的 cycles、resources、operand timing 與 bypass 來自固定 compiler/runtime source；不公開或未證實的實體 pipeline stage、clock、link bandwidth、hop latency、FIFO depth 均標為未知。`IssueWidth=1000` 等 scheduler sentinel 不解讀為硬體千路發射。

本專案未安裝 toolchain、未編譯或執行 NPU kernel、未下載模型權重，也未修改 driver、kernel、BIOS 或 ROCm。計算器是容量／效能下界模型，不是 benchmark。

## 授權與來源

文章與產生器引用的每項技術主張皆附來源。LLVM／MLIR-AIE／AIE-RT 等上游程式碼受各自授權條款約束；見 `wiki/spec-NOTICES.txt` 與來源 repository。此 repository 不提供法律或商用授權保證。
