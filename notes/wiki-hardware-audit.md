# XDNA2 硬體八頁 Wiki 來源查核

## 交付與權限

本工作僅撰寫 `wiki/content/hardware.json` 與本檔。已完整閱讀 `notes/WIKI-PLAN.md`、`notes/type-mma-audit.md`，直接查閱本地 source snapshots；沒有委派其他作者、修改 sources/site/build scripts、操作服務、建置編譯器或執行 NPU。沒有新增網路研究，因本地固定版本已足以支持本文採用的主張。

JSON 是八筆 article record 的陣列，順序為 `system, compute, memory, dma, synchronization, isa, datatypes, mma`；前六頁為「架構」，末兩頁為「數值」，全部標記「來源查核」。文內以「來源事實」和「工程推論／數學推論」區別證據與設計建議。正常中文解釋的字符量以正文漢字計數，不將 URL、英文字母或來源表充作中文字數。

本文的 typed-claim 邊界遵從既有型別稽核：型別表示、原生算術、原生 matrix primitive、API 合成、編譯器降精度及 libcall 是不同層級。來源與測試中出現的 measured、native、INTRINSIC、accuracy_safe，均不自動提升為晶片實測或數值完全相容保證。

## 固定版本與核對方法

以下 SHA 由各 repository 的 `git rev-parse HEAD` 取得，不從稽核筆記推定。它們與既有型別稽核一致，但沒有驗證可組成同一套可建置工具鏈。

| Snapshot | Immutable commit |
|---|---|
| `sources/mlir-aie` | `0ed8e7e477fd9094acee8dada7ab81604a7fb07a` |
| `sources/llvm-aie` | `386ca5c6634a84bb224b7248e79df8edabf0722f` |
| `sources/aie_api` | `bec000fd312b407c61f25ef86fd582042e42d28a` |

先閱讀 AIETargetModel 的繼承／NPU2 類別、architecture reference、完整 `core_data_memory.md`、完整 Peano README，再對照 AIE2P headers、API specialization、lowering、instruction patterns 及 FileCheck 文字。每條引用採 GitHub `blob/<40-character SHA>/<path>#Lx-Ly`，行號為 1-based、含兩端。

對 JSON 全部引用檔案執行唯讀核對：本地 bytes 必須等於 `git show SHA:path`，引用行號必須在檔案範圍內，SHA 必須等於 HEAD。三個 source 工作樹在核對時 `git status --short` 均無輸出。專案根目錄本身不是 Git repository，所以沒有以根目錄 diff 冒充全工作區檢查。

## 頁面責任與主要證據

| 頁面 | 主要可確認內容 | 主證據定位 |
|---|---|---|
| system | AIE2P target、完整 Strix 列角色與可變欄分區；memory affinity 不等於 routing | `llvm-aie/README.md:1–66`；`AIETargetModel.h:1077–1145`；`.cpp:755–824,885–949` |
| compute | Scalar/SIMD/VLIW 分層、容器與 accumulator、helper 成本及排程限制 | `AIE2PRegisterInfo.td:109–132`；`accum_native_types.hpp:15–24,167–172`；`emulated_mmul_intrinsics.hpp:207–269` |
| memory | Program/data 分離、共用資料區、連續空間、banks 與對齊 | `AIETargetModel.h:749–790,830–834,1077–1145`；`core_data_memory.md:10–176,193–218`；`ld_st.hpp:33–40` |
| dma | BD、direction/index channel、ND 單位與限制、鎖生命週期 | `AIEOps.td:940–1064,1291–1347`；`AIETargetModel.h:759–824` |
| synchronization | Counting semaphore、greater-equal 語意、局部深度／重疊、等待圖 | `AIEOps.td:1500–1611`；`aie2p_locks.h:14–61`；ObjectFifo 教學 `258–298`；trace 文件 `75–101` |
| isa | Header→builtin→pattern、legalization、guard、排程及 i16 靜態疑點 | `AIE2PInstrPatterns.td:295–307,422–427,443–460`；`AIE2PLegalizerInfo.cpp:214–255`；`AIEVecToLLVM.cpp:4895–4904,4980–5048` |
| datatypes | INT4 解包、BF16/BFP16 表示、FP32 分解與降精度、rounding | `aie2p_vmult.h:39416–39509,53918–53994,54935–54942`；`aie_doc.hpp:229–250`；`aie_types.hpp:34–60` |
| mma | M/K/N、dense 代表形狀、非 BFP helper、BFP T 原語及不同 lowering | `aie.hpp:6295–6530`；`mmul_bf16_bf16.hpp:63–178`；`mmul_bfp16_bfp16.hpp:17–104`；`matmul-aie2p.mlir:10–166` |

上表使用簡寫；下方完整索引列出 repository、完整相對路徑、行號與 immutable URL，可避免不同 repository 的同名檔案混淆。

## 決策與不採用的延伸

1. **容量與拓撲限定為 compiler model。** 64 KiB data、16 KiB program、512 KiB mem tile；完整 Strix 八欄、四個 compute rows。VirtualizedNPU2 使用指定 cols，不能所有 SKU／部署一律乘完整核心數。
2. **Banks、地址視窗、bus、alignment 四者分開。** Model 回傳 mem tile 八 banks、其他 tile 四 banks；East=self，memory affinity 受邊界限制。256-bit load/store bus model 不等於 full-width 512-bit alignment，也不等於量測頻寬。鄰接視窗不是核心新增私有容量。
3. **不採速查表的固定 L1/L2/DDR 延遲、固定時脈及 BF16 MAC/cycle。** API 算術次數與數學 MAC／原語工作量可以計算，但沒有 issue-rate／pipeline II／動態停頓證據。Scheduler destination/source timing 不能改寫成 mmul latency。
4. **程式與資料空間不能相加。** Stack、ObjectFifo backing buffers、手動 buffers、核心 sections 共用 data。`data_size` 要求連續 run；stack measured attribute 是 linked ELF 靜態分析。Override 與關閉檢查不是越界安全證明。
5. **DMA BD 不是 channel，也不是 lock。** Mem/core/shim 的 BD 與 ND 維度取自 model；mem tile channel parity 有 BD 半區可達性限制。不發布未追完 lowering 單位的最大傳輸 bytes 表，也不把 scratchpad affinity 當成跨欄 DMA 路由定理。
6. **BF16 非 BFP helper 必須保留。** `4×8×8` 是八次 32-lane 算術及重排；非 macro `8×8×8` 是兩份 helper。BFP macro 路徑會轉共享指數，不是免費／完全等價替身。
7. **BFP16 格式與 matrix 能力分層。** EBS8 每八個 signed 8-bit mantissa 共享 exponent，共九 bytes；六十四個值共七十二 bytes／576 bits。EBS16 緊縮記憶體與重複 exponent 的 register 表示不同。EBS16 forwarding declaration 不保證全部 EBS8 shapes 可用。
8. **INT4 保留 unpack 路徑的細節與範圍。** 本 Peano 8b×4b `4×16×16` 先 unpack 為 int8，再做兩個 int8 matrix 運算；不宣稱 dense 4b×4b 原語或固定 MAC/cycle，也不據此否定其他工具鏈／未公開晶片能力。
9. **FP32 不只一種模擬。** API float path 為 BF16 多部分積 emulation；Peano default accuracy_safe 有九個部分乘積及其他轉換／殘差操作。MLIR 通用 bf16-emulation 是 truncf/op/extf，FMA 連 acc 都截斷。FP32 accumulator/output 不證明 native FP32-input multiply。
10. **Arch 21 與 arch 22 隔離。** 共用 header 的 `_Float16`、float8、bfloat8 受 arch 22 guard；不將 FP16／FP8／MX 移入本次 XDNA2 能力。未見支援只代表此 snapshot 與查核範圍缺證，不是對其他工具鏈或未公開硬體的不存在證明。
11. **i16 signedness 僅是未重現疑點。** Decoder 的 `8×2×8` 固定 conf=24，rewrite 沿用；對照 Peano sign bits 存在靜態風險。沒有執行 regression，不能稱晶片 bug，不能概括否定 C++ signed i16 API。正文明示限定路徑。
12. **不混 sparse 與 dense。** 本表是代表性 dense shape；較小 API 可能抽取較大原語子集，不能把 API 數量當作機器指令目錄。

## 文件落差與待補證據

- **Architecture reference 是導航，不是最高層規格。** 路由絕對敘述、FIFO 實務深度、延遲／頻率表及 BF16 peak 不由已讀 target model／primitive 支持，正文沒有照抄。
- **DMA stride 文內落差。** `AIEOps.td:1029` 的示例出現最內 stride=2，而 `1044` 的 gotcha 文字要求最內 stride=1。本文只說須核對限制，沒有據示例宣稱所有 tile 接受任意 inner stride。需另追 verifier、字寬換算與對應配置產物，本工作不跑工具鏈。
- **ObjectFifo 範例只作局部容量說明。** `section-2/section-2a/README.md:258–298` 討論概念深度與並行；示例 producer／consumer 的有限迴圈各重複相同次數，但消費者每次取得更多物件。不能把該段直接當成完整有限工作量的活性證明。正文明列總物件數、啟動／穩態／排空及尾端行為須另查。
- **Macro 層次落差。** MLIR-AIE kernel 用 `#ifdef`，API 用 `#if`；`-D...=0` 在兩層不同。直接 AIEVec BF16 lowering 又不是同一 C++ preprocessor 路徑，須保留各自形狀與精度契約。
- **版本整合未知。** 三組 SHA 的 API、Peano ABI、headers、runtime libcall 與整套連結相容性未建置驗證。FileCheck 只閱讀預期，沒有宣稱通過。
- **物理細節未知。** 完整 bank 微架構、仲裁、實際可用分區、clock／power 狀態、DMA routing 全部合法集合、有效頻寬、load/store latency、pipeline II、register spill 與 stall 比例沒有實測。
- **數值邊界未知。** NaN、Inf、subnormal、signed zero、tie、overflow／underflow、各 conversion 的完整誤差及 IEEE bit-exact 行為未驗證。LLM 模型品質與量化資料集結果亦未量測。
- **活性與一致性未知。** 未重現 deadlock、未跑 trace、未驗證主機 cache coherence／完成語意。timeout 不能單獨證明死鎖，鎖 header pointer overload 不代表主機同步契約。

## 靜態交付檢查

已以不落地建置產物的 Python 檢查 JSON schema、exact slugs/order/category/status、正文漢字量、章節數、來源數、所有內文外部引用均在 sources、所有內部連結及 related 都屬 plan 的 26 slugs、引用行號範圍，以及本地引用檔案與 immutable git blob 的 bytes 相同。檢查不是 compiler build、不是 NPU 測試，也不是整站／瀏覽器驗收。

完整結果與來源索引列於下方。

### 最終檢查結果

| slug | 正文漢字數 | 二級章節 | Immutable references | Markdown 表格 |
|---|---:|---:|---:|---:|
| system | 1421 | 6 | 6 | 1 |
| compute | 1425 | 7 | 11 | 1 |
| memory | 1414 | 7 | 9 | 1 |
| dma | 1454 | 7 | 6 | 1 |
| synchronization | 1495 | 7 | 7 | 1 |
| isa | 1465 | 7 | 17 | 1 |
| datatypes | 1445 | 7 | 24 | 1 |
| mma | 1486 | 8 | 20 | 1 |

共 57 個不同 immutable 行號範圍、32 個引用檔案；全部與 pinned Git blob 位元組一致。正文 Markdown 以 `markdown` 的 fenced_code/tables 擴充在記憶體解析，再用 BeautifulSoup 檢查章節、表格及連結。沒有輸出 HTML、執行站台 builder 或操作瀏覽器。

編修期間的靜態檢查曾找到一個 accumulator 引用尾端超出檔案範圍，以及 ISA 頁缺少表格；已分別縮到實際 FP storage 行號與補上證據層級表，最終重新檢查通過。這些是文稿修正，不是 compiler／硬體缺陷。

### 完整 source-to-claim 索引

下表行號均相對固定 SHA；連結文字包含本地完整路徑。不同範圍即使同檔仍分列，以保留主張的可追蹤性。

| 主張／證據 | 路徑、行號與 immutable URL | 使用頁面 | 限制／備註 |
|---|---|---|---|
| AIE API：公開 MMUL 契約 | [`sources/aie_api/include/aie_api/aie.hpp:6295–6530`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/aie.hpp#L6295-L6530) | datatypes, mma | M/K/N、size_A/B/C、mul 初始化、mac 累加、普通 vector row-major 及浮點 shift 忽略。 僅靜態來源查核。 |
| AIE API 格式表：BFP block bytes | [`sources/aie_api/include/aie_api/aie_doc.hpp:229–250`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/aie_doc.hpp#L229-L250) | datatypes | EBS8 八 mantissas 加共享 exponent 共九 bytes；EBS16 十七 bytes。 僅靜態來源查核。 |
| AIE API：rounding／saturation | [`sources/aie_api/include/aie_api/aie_types.hpp:34–60`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/aie_types.hpp#L34-L60) | datatypes | Floor 與 toward-zero 不同；deprecated truncate=saturate；中間溢位與輸出飽和分開。 僅靜態來源查核。 |
| AIE API：累加型別映射 | [`sources/aie_api/include/aie_api/detail/aie2p/accum_native_types.hpp:15–24`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/accum_native_types.hpp#L15-L24) | compute, datatypes | acc16/24→acc32，acc40/48/56→acc64；型別標籤不等於多種物理位寬。 僅靜態來源查核。 |
| AIE API：浮點累加儲存 | [`sources/aie_api/include/aie_api/detail/aie2p/accum_native_types.hpp:167–172`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/accum_native_types.hpp#L167-L172) | compute | FP accumulator 的每 lane 32-bit storage specialization 與較大組合表示。 僅靜態來源查核。 |
| AIE API：FP32 feature guards | [`sources/aie_api/include/aie_api/detail/aie2p/config.hpp:22–24`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/config.hpp#L22-L24) | isa, datatypes | FP32 emulation guard 與 native support=0 分離；非所有 FP32 表示皆不支援。 僅靜態來源查核。 |
| AIE API：寬整數部分積合成 | [`sources/aie_api/include/aie_api/detail/aie2p/emulated_mmul_intrinsics.hpp:10–122`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/emulated_mmul_intrinsics.hpp#L10-L122) | mma | 32×32、較大 K 的 32×16、16×32 代表 helper 以高低字、shift 與多次原語合成。 僅靜態來源查核。 |
| AIE API：非 BFP BF16 helper | [`sources/aie_api/include/aie_api/detail/aie2p/emulated_mmul_intrinsics.hpp:207–269`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/emulated_mmul_intrinsics.hpp#L207-L269) | compute, datatypes, mma | 4×8×8 的八次 32-lane MUL/MAC，加 broadcast/shuffle；無 cycle 保證。 僅靜態來源查核。 |
| AIE API：i16 shape 與 accumulator | [`sources/aie_api/include/aie_api/detail/aie2p/mmul_16_16.hpp:23–105`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/mmul_16_16.hpp#L23-L105) | datatypes, mma | 8×2×8 acc32、4×4×8 內部 acc64；較小 shape 可取較大原語子集。 僅靜態來源查核。 |
| AIE API：BF16 轉 BFP16 路徑 | [`sources/aie_api/include/aie_api/detail/aie2p/mmul_bf16_bf16.hpp:63–131`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/mmul_bf16_bf16.hpp#L63-L131) | datatypes, mma | macro 開啟後 transpose B、轉 accfloat/BFP16 再呼叫 BFP 原語，涉及精度變化。 僅靜態來源查核。 |
| AIE API：非 BFP 大形狀 | [`sources/aie_api/include/aie_api/detail/aie2p/mmul_bf16_bf16.hpp:134–178`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/mmul_bf16_bf16.hpp#L134-L178) | mma | macro=0 仍有 8×8×8，分兩份 4×8×8 helper。 僅靜態來源查核。 |
| AIE API：BFP16 MMUL specialization | [`sources/aie_api/include/aie_api/detail/aie2p/mmul_bfp16_bfp16.hpp:17–104`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/mmul_bfp16_bfp16.hpp#L17-L104) | datatypes, mma | EBS8 8×8×8 直接 T 原語、8×8×16 兩次原語；EBS16 forwarding 不保證所有 shape 成功。 僅靜態來源查核。 |
| AIE API：FP32 MMUL emulation | [`sources/aie_api/include/aie_api/detail/aie2p/mmul_fp32_fp32.hpp:24–44`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/aie2p/mmul_fp32_fp32.hpp#L24-L44) | datatypes, mma | 4×8×4 specialization 在 FP32_EMULATION guard 內。 僅靜態來源查核。 |
| AIE API：AIE2P load/store 對齊 | [`sources/aie_api/include/aie_api/detail/ld_st.hpp:33–40`](https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/include/aie_api/detail/ld_st.hpp#L33-L40) | compute, memory | 不同向量寬度的對齊 helper；full-width 64-byte alignment 不等於匯流排寬度。 僅靜態來源查核。 |
| Peano README：架構與後端 | [`sources/llvm-aie/README.md:1–66`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/README.md#L1-L66) | system, compute, synchronization, isa | XDNA2 target triple、in-order exposed-pipeline VLIW、編譯器責任及成熟度限制。示例 timing 非本次硬體規格。 僅靜態來源查核。 |
| Peano AIE2P locks：builtin 包裝 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_locks.h:14–61`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_locks.h#L14-L61) | synchronization | Greater-equal 的負值編碼及 pointer overload；不應按負號猜測邏輯計數初值。 僅靜態來源查核。 |
| Peano：浮點／BFP conversion | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_srs.h:1281–1344`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_srs.h#L1281-L1344) | datatypes | 專用 BF16 conversion，BFP conf helper save/set/restore rounding；非全 IEEE 邊界保證。 僅靜態來源查核。 |
| AIE2P 版本標頭 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_version.h:14–20`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_version.h#L14-L20) | system, isa, datatypes | arch 21 與 model 巨集；不可混用 arch 22。 僅靜態來源查核。 |
| Peano：i8 matrix builtin 與 sign bits | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:15–58`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L15-L58) | isa, datatypes, mma | 8×8×8 integer builtin、configuration 的 signX/signY；sign control 與 bit container 分開。 僅靜態來源查核。 |
| Peano：i32×i16 直接原語 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:37603–37651`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L37603-L37651) | mma | 4×2×8→32×acc64，直接 I512_I512_ACC2048 builtin。 僅靜態來源查核。 |
| Peano：BFP16 matrix builtin | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:38830–38885`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L38830-L38885) | isa, mma | 8×8×8T 傳遞 mantissa/exponent 至 BFP576 builtin，回傳 accfloat。 僅靜態來源查核。 |
| Peano：8b×4b wrapper 展開 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:39416–39509`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L39416-L39509) | compute, isa, datatypes, mma | 4×16×16 先 unpack/shuffle，再兩次 4×8×16 int8 算術；不是單一 INT4 MMA 證據。 僅靜態來源查核。 |
| Peano：FP32 的 BF16 部分積 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:53918–53994`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L53918-L53994) | isa, datatypes | Safe path 九個部分乘積加總，另有殘差/轉換；與單次 BF16 truncation 不同。 僅靜態來源查核。 |
| Peano：float wrapper 預設選擇 | [`sources/llvm-aie/clang/lib/Headers/aie2p/aie2p_vmult.h:54935–54942`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L54935-L54942) | isa, datatypes, mma | mul_elem_32(v32float,...) 預設 accuracy_safe。 僅靜態來源查核。 |
| Peano：四位元 scalar typedef | [`sources/llvm-aie/clang/lib/Headers/aiebase_typedefs.h:117–118`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aiebase_typedefs.h#L117-L118) | datatypes | signed/unsigned _BitInt(4) 表示存在；不保證 scalar 陣列即 packed vector layout。 僅靜態來源查核。 |
| Peano：BF16 與 packed INT4 typedef | [`sources/llvm-aie/clang/lib/Headers/aiebase_typedefs.h:235–270`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aiebase_typedefs.h#L235-L270) | datatypes | __bf16；v256int4 的 128-byte storage、其他 nibble 容器。 僅靜態來源查核。 |
| Peano：BFP16 register 表示 | [`sources/llvm-aie/clang/lib/Headers/aiebase_typedefs.h:545–578`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aiebase_typedefs.h#L545-L578) | datatypes | EBS16 exponent 在 register 中重複，不等於緊縮記憶體大小。 僅靜態來源查核。 |
| Peano：arch 22 FP16／FP8 guard | [`sources/llvm-aie/clang/lib/Headers/aiebase_typedefs.h:580–643`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aiebase_typedefs.h#L580-L643) | isa, datatypes | _Float16、float8、bfloat8 在 arch 22 區塊；不可移植為 arch 21 支援。 僅靜態來源查核。 |
| AIE2P itinerary：VMAC operand timing | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PGenSchedule.td:9031–9064`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PGenSchedule.td#L9031-L9064) | compute, isa, mma | 來源／目的 operand timing 與 bypass 是 scheduler 模型；不可讀成 mmul 固定耗時或 issue-rate。 僅靜態來源查核。 |
| AIE2P patterns：寬向量 BF16 | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td:295–307`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td#L295-L307) | compute, isa | VEC1024／ACC2048 的 BF16 VMUL/VMAC selection，容器位寬不等於矩陣工作量。 僅靜態來源查核。 |
| AIE2P patterns：I512 integer VMUL／VMAC | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td:422–427`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td#L422-L427) | mma | 整數 matrix intrinsic 對應機器 selection，與 i8 及 i32×i16 header 對照；不證明每週期吞吐量。僅靜態來源查核。 |
| AIE2P patterns：BFP VMUL／VMAC | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td:443–460`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PInstrPatterns.td#L443-L460) | isa, mma | BFP576 intrinsic 到機器 pattern；不是 helper 或 kernel 耗時。 僅靜態來源查核。 |
| AIE2P legalizer：scalar FP 路徑 | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PLegalizerInfo.cpp:214–255`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PLegalizerInfo.cpp#L214-L255) | isa, datatypes | Scalar BF16 MUL 向量化後抽取；FP32/FP64 MUL 有 libcall。不能保證部署可連結。 僅靜態來源查核。 |
| AIE2P 後端：scalar register class | [`sources/llvm-aie/llvm/lib/Target/AIE/aie2p/AIE2PRegisterInfo.td:109–132`](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/llvm/lib/Target/AIE/aie2p/AIE2PRegisterInfo.td#L109-L132) | compute, isa | 一般暫存器類別存在；不等於獨立 scalar 執行緒或 FP32 原生乘法。 僅靜態來源查核。 |
| MLIR-AIE kernel：BF16 macro 幾何 | [`sources/mlir-aie/aie_kernels/aie2p/mm.cc:437–487`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/aie_kernels/aie2p/mm.cc#L437-L487) | mma | Kernel 使用 #ifdef、API 使用 #if，定義為零不等同未定義。 僅靜態來源查核。 |
| AIE DMABDOp：描述子與布局契約 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIEOps.td:940–1064`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIEOps.td#L940-L1064) | dma, synchronization | Buffer、offset/len、元素單位、BD 鏈與 ND layout；文件內 stride 例子與限制文字有落差，本文不判定所有可用步距。 僅靜態來源查核。 |
| AIE DMAStartOp：通道契約 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIEOps.td:1291–1347`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIEOps.td#L1291-L1347) | dma | 通道由 MM2S/S2MM 方向與 index 定義；channel、BD 與 per-channel padding 分層。 僅靜態來源查核。 |
| AIE LockOp／UseLockOp：鎖語意 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIEOps.td:1500–1611`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIEOps.td#L1500-L1611) | synchronization | Counting semaphore、AcquireGreaterEqual 等待後扣除、Release 增加；非主機 mutex/coherence 保證。 僅靜態來源查核。 |
| AIETargetModel：核心容量與地址 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIETargetModel.h:749–790`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIETargetModel.h#L749-L790) | compute, memory | 64 KiB data、16 KiB program、地址視窗、256-bit load/store bus 及 cascade 模型；非存取延遲量測。 僅靜態來源查核。 |
| AIETargetModel：鎖與 BD 資源 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIETargetModel.h:759–824`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIETargetModel.h#L759-L824) | dma, synchronization | 鎖、BD 數、ND 維度及 mem tile channel 對 BD 半區的可達性。 僅靜態來源查核。 |
| AIETargetModel：mem tile 容量與 banks | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIETargetModel.h:830–834`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIETargetModel.h#L830-L834) | memory | 512 KiB mem tile；模型回傳 mem tile 八 banks、其他 tile 四 banks。 僅靜態來源查核。 |
| AIETargetModel：NPU2 拓撲與分區 | [`sources/mlir-aie/include/aie/Dialect/AIE/IR/AIETargetModel.h:1077–1145`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/include/aie/Dialect/AIE/IR/AIETargetModel.h#L1077-L1145) | system, memory | 完整 Strix 八欄、六列角色、可變 cols 分區及 512-bit 對齊；不是所有 SKU 或 runtime 配額。 僅靜態來源查核。 |
| MLIR i16 decoder：未重現疑點 | [`sources/mlir-aie/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp:4895–4904`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp#L4895-L4904) | isa, datatypes, mma | 8×2×8 回傳固定 conf=24，未像 i8 合入 sign bits；靜態疑點，不是晶片 bug。 僅靜態來源查核。 |
| MLIR i16 rewrite：conf 沿用 | [`sources/mlir-aie/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp:4980–5048`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp#L4980-L5048) | isa | 取得 decoded conf 並加入 padded operands；用於限定 signedness 疑點所在路徑。 僅靜態來源查核。 |
| MLIR AIEVec rewrite：BFP helper | [`sources/mlir-aie/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp:5048–5095`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp#L5048-L5095) | mma | 直接 BF16 lowering 的轉換、B 轉置及 BFP helper，與 C++ macro 路徑分開。 僅靜態來源查核。 |
| AIETargetModel：記憶體鄰接 | [`sources/mlir-aie/lib/Dialect/AIE/IR/AIETargetModel.cpp:755–824`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Dialect/AIE/IR/AIETargetModel.cpp#L755-L824) | system, memory, dma | East=self、方向與邊界／mem tile 例外；不可推成完整 DMA 路由限制。 僅靜態來源查核。 |
| AIETargetModel：switchbox 目的埠 | [`sources/mlir-aie/lib/Dialect/AIE/IR/AIETargetModel.cpp:885–949`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Dialect/AIE/IR/AIETargetModel.cpp#L885-L949) | system, dma | 各 tile 的方向／DMA 連接資源與邊界；不是完整路由可行性證明。 僅靜態來源查核。 |
| MLIR：通用 bf16-emulation rewrite | [`sources/mlir-aie/lib/Dialect/AIEVec/Transforms/VectorToVectorConversions.cpp:812–943`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Dialect/AIEVec/Transforms/VectorToVectorConversions.cpp#L812-L943) | datatypes | Binary ops truncf/op/extf；vector.fma 三個 operands 包括 acc 都截成 BF16。 僅靜態來源查核。 |
| Core Data Memory：共用資料區 | [`sources/mlir-aie/programming_guide/core_data_memory.md:10–32`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/core_data_memory.md#L10-L32) | memory | Stack、buffers、.data/.rodata/.bss 共用本地 data memory。 僅靜態來源查核。 |
| Core Data Memory：stack 分析 | [`sources/mlir-aie/programming_guide/core_data_memory.md:34–105`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/core_data_memory.md#L34-L105) | memory | Linked ELF 靜態呼叫路徑分析、缺失資料與 override；measured 屬編譯分析，不是 runtime 測量。 僅靜態來源查核。 |
| Core Data Memory：連續區間與預建 ELF | [`sources/mlir-aie/programming_guide/core_data_memory.md:107–176`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/core_data_memory.md#L107-L176) | memory | data_size 保留一段連續區間；預建 ELF 固定地址須另保留，不能只用大小表達。 僅靜態來源查核。 |
| Core Data Memory：配置策略 | [`sources/mlir-aie/programming_guide/core_data_memory.md:193–218`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/core_data_memory.md#L193-L218) | memory | bank-aware、basic-sequential、mem_bank 的不同處理；不提供 bank 延遲。 僅靜態來源查核。 |
| ObjectFifo：概念深度與局部池 | [`sources/mlir-aie/programming_guide/section-2/section-2a/README.md:258–298`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/section-2/section-2a/README.md#L258-L298) | synchronization | 批量取得、可前進與可重疊所需容量不同；範例不是完整有限迴圈活性證明。 僅靜態來源查核。 |
| Trace 文件：等待事件分類 | [`sources/mlir-aie/programming_guide/section-4/section-4b/README.md:75–101`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/section-4/section-4b/README.md#L75-L101) | synchronization | Memory、stream、lock stall 名稱；僅讀文件，未取得任何硬體 trace。 僅靜態來源查核。 |
| 架構速查表：交叉查核對象 | [`sources/mlir-aie/skills/aie-code-creator/references/architecture.md:39–142`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/skills/aie-code-creator/references/architecture.md#L39-L142) | system, compute, dma | 用於導航與自然向量寬度；固定 clocks、latencies、BF16 MAC/cycle、路由絕對規則及 FIFO 深度不採作保證。 僅靜態來源查核。 |
| MLIR FileCheck：BF16 matmul 預期 | [`sources/mlir-aie/test/Conversion/AIEVecToLLVM/matmul-aie2p.mlir:10–166`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/test/Conversion/AIEVecToLLVM/matmul-aie2p.mlir#L10-L166) | mma | 4×8×8／8×8×8 預期 BFP conversion；其他形狀預期多次 BF16 MAC。未執行。 僅靜態來源查核。 |
| MLIR FileCheck：i8 signedness 預期 | [`sources/mlir-aie/test/Conversion/AIEVecToLLVM/matmul-aie2p.mlir:169–232`](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/test/Conversion/AIEVecToLLVM/matmul-aie2p.mlir#L169-L232) | isa, datatypes | 四組 configuration 與 signless 預設 signed；只讀預期、未執行測試。 僅靜態來源查核。 |
