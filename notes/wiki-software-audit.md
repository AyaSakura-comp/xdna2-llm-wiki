# Software wiki source audit

## 範圍、狀態與所有權

- 僅撰寫 `wiki/content/software.json`、`notes/wiki-software-audit.md`，沒有修改 sources、site、建置腳本、服務或相依套件；沒有委派。
- 已讀 `notes/WIKI-PLAN.md`、`site/guide-notes.md`、Triton-XDNA README、Qwen README／完整 model.py／全部 kernels/*.py、zero_copy 兩支程式與 common/add_chain.py，以及 MLIR-AIE programming_guide 的編譯、HSA、HRX、結構、FIFO、Runtime tasks、記憶體與 trace 相關段落。
- 七個 slug：compiler、iron、triton、runtime、llm-graph、qwen-case、debug。前四與 debug 為「程式設計」；另外兩篇為「LLM推論」。全部 status 為「來源查核」，不是實測。
- 來源閱讀與靜態 JSON／連結檢查已完成；未安裝模型、未下載權重、未編譯 kernel、未跑 NPU、未測 runtime availability、未修改 ROCm／驅動／BIOS。文章內命令只是 source-checked examples。
- 未做 live web 查詢；外部來源及遠端 HEAD 比較留給主整合者。使用者所述 live README 矛盾在本地固定快照亦確實存在，但不把這項確認寫成重新查過遠端。

## 固定來源與版本配對

本機 `git rev-parse HEAD` 結果：

| 倉庫 | HEAD | 證據狀態 |
|---|---|---|
| Triton-XDNA | `5c33df1263f29de30f71616780c2e8a88e623782` | 本地確認；符合預期 5c33… |
| mlir-aie | `0ed8e7e477fd9094acee8dada7ab81604a7fb07a` | 本地確認 |
| mlir-air | `ff95a9b35b692b4cfbdf1d52bf69e6ffe01facde` | 獨立來源快照，不宣稱是 Triton 相容相依版本 |
| llvm-aie | `386ca5c6634a84bb224b7248e79df8edabf0722f` | 本地確認；稀疏來源，不是完整離線建置套件 |

另查 Triton、AIE、Peano 的 `git diff --name-only HEAD` 無 tracked 修改，故引用的本地內容對應固定 commit。研究根目錄本身不是 Git repository，不能從根目錄 `git status` 宣稱整個專案乾淨；此限制不影響子倉庫 SHA 查核。

[Triton AIR lock](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/utils/mlir-air-hash.txt) 是 commit `6746658`，Version `0.0.1`、Timestamp `2026090504`；[Peano lock](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/utils/peano-requirements.txt) 為 `llvm-aie==22.0.0.2026090201+a36c62b9`。不能把上表 independently downloaded HEADs 視為已一起建置／測試的組合。文章未推薦安裝 nightly 或替換本機 ROCm。

## Qwen：以分支裁決 README 與註解

以下均為 `sources/Triton-XDNA/examples/qwen2_5/` 下固定快照行號。主來源：[model.py](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/qwen2_5/model.py)、[README](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/qwen2_5/README.md)。

| 檔案／行號 | 查核結果 | 狀態及限制 |
|---|---|---|
| README Backend Modes／Per-Op Routing 與表後段落 | 新表寫 npu=CPU+NPU，hetero-fast decode GPU；舊段落仍把 attention／LM head 說成 always iGPU | 已確認文字互相矛盾；正文不照抄舊句 |
| model.py:826–846、889–927 | npu 的 QKV／O backend 是 npu；CPU f32 scores、torch.softmax、attn@V；其餘走 GPU fused attention | 可執行分支優先，非硬體實測 |
| kernels/rope.py:43–67 | cos/sin 移往 q.device，輸出依 q/k dtype；不是強制 GPU | 檔頭「every backend GPU」過時 |
| model.py:1124–1142 | hetero LM head GPU；npu LM head 為 CPU torch matmul | 初始化附近 npu LM head 在 NPU 的註解亦過時；不採其註解中的速度數字 |
| model.py:929–977 | decode_gpu 條件是 backend==hetero-fast 且 S==1 | 一 token prompt 也會符合，不能只按 prefill/decode 名稱推理 |
| model.py:982–1051 | hetero 分支有 to_gpu／to_cpu，且可選 fused tail | 不宣稱自動 zero-copy |
| model.py:1053–1104，尤其 1065 | 一般 gpu/npu 分支無條件將 attn_out 送 CPU | fullGPU 是名義主算子路由，不是沒有主機往返；GPU add wrapper 再搬回 GPU。僅靜態發現，未實測代價 |
| model.py:196、649–652、1011–1020、1072–1077 | fused BM=128；FUSED_MLP env 預設 "1"；真實 B×S 必須不超過 BM | opt-in 註解過時；長輸入走未融合路徑 |
| model.py:298–329、331–490、554–561 | gamma 折進 gate/up 權重；tail chain 含 add、norm、MLP 與下一層 bare norm；按 layer 管理 static weight BO | 不把 chain 叫成單一 machine instruction，亦不照抄舊「五 dispatch」註解 |
| model.py:732–824 | linear/norm/swiglu/add/softmax helpers 有 try/except，warning 後 PyTorch fallback | fallback != NPU execution；PyTorch 用當下 tensor device，仍可能拋錯 |
| model.py:917–921、1022、1079；kernels/attention.py | 直接 fused attention 與 fused_mlp.run 沒有同等 try/except | README「每個 wrapper 都有 fallback」過度概括，正文明確排除 |
| model.py:875–887、1146–1219 | 預配置 KV，原地追加，再 repeat_interleave 展開供注意力使用；generate 分別計時 prefill/decode | 理想 KV payload 不含展開暫存；未宣稱已測記憶體峰值 |
| kernels/matmul.py:232–319 | 獨立 NPU matmul M/N 補齊 256，K 為 next pow2，full-K launch，f32 output | 與 fused BM=128 分開；不推導實際 NPU 吞吐 |
| kernels/rmsnorm.py:61–93、145–193 | bare norm 除以真實欄數，wrapper CPU gamma multiply | 「RMSNorm 在 NPU」須註明主機輔助；f32 算式不是原生 f32 multiply 的證據 |
| kernels/swiglu.py:118–160；kernels/add.py:100–136 | 獨立 NPU SwiGLU 兩段；NPU add 可選 f32 | 不把獨立版本的型別／dispatch 數套到融合鏈 |
| kernels/softmax.py:131–188 | NPU wrapper 最少補到128欄、四列 chunk、裁切後重正規化 | 只存在 wrapper；Qwen npu attention 未使用它。小 buffer timeout 註解不能泛化為 DMA 規格 |
| kernels/backend_utils.py:47–70 | key 是 grid 和 kwargs constexpr，後續直接 mod.launch | 未含所有 positional constexpr 語意；移植形狀時須另審，不宣稱已動態重現 collision |

[CLI 固定來源](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/qwen2_5/qwen_inference.py)：119–162 印 max/mean error、cosine、top-k；349–443 預設 npu、max-tokens=0，cosine floor 0.95，沒有 top-1 assertion；max-tokens>0 的生成路徑沒有同樣品質閘門。`cos_sim < COS_MIN` 也不是完整 NaN 拒絕檢查，正文把有限值檢查列為工程建議，而非既有 assertion。

計時：CLI 202–225 將 prefill forward 記為 TTFT，TPOT 是 decode_times 平均，TPS 包含 prefill，steady TPOT 排除第一次 decode。model.generate 在 KV allocation 後才開始 prefill timer。模型載入／tokenization 不在此 TTFT；首次 JIT、context、cache state 必須另外記錄。不得把 hetero-fast 的 GPU decode 當 NPU decode 成績，不得將 fullGPU、CPU+NPU、hetero 混成單一量測基準。

## 編譯、產物、ABI

- [MLIR-AIE compilation_stages](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/compilation_stages.md)：recipe／artifact hash、as_mlir／compile／call 區分；逐核心 ELF、insts ELF、PDI、xclbin 各有不同角色。預設 XRT 的 NPUKernel 外部產物路徑沒有 JIT tensor-size metadata，不能保證形狀正確。
- [aiecc README:29–49](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/tools/aiecc/README.md#L29-L49)：xclbin + per-sequence insts 與 full-ELF 是不同輸出。沒有把所有 ELF 視為同一封裝。
- [Triton driver.py:1093–1133](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/amd_triton_npu/backend/driver.py#L1093-L1133)：XRT auto=npu2 ELF／npu1 xclbin；HSA 強制 PDI + insts 並拒絕衝突的 ELF/xclbin 設定。
- [IRON HSA](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/hsa_runtime.md) 與 [HRX](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/programming_guide/hrx_runtime.md)：HSA PDI consumer 是明列的另一 backend，不能套用預設 XRT「PDI 非 run input」概括句。HRX 使用 libhrx／amdxdna HAL 與 xclbin + insts；不是 Peano，也不是 AIR 編譯層。
- IRON 使用 NPU_RUNTIME，Triton 使用 AMD_TRITON_NPU_RUNTIME 或 NPUDriver(runtime)，不交換設定名稱。HSA 需 AIE-capable ROCR／agent／extension ABI，不假設本機 ROCm 已具備。
- IRON HSA 文件記載 in-order queue、system-scope acquire/release fences、該 ROCR 同步 doorbell、呼叫者序列化要求及無 trace capture。HRX 文件明列 flush/invalidate、execution+memory barriers。都是來源描述，未做本機 availability 或行為測試。

## Shared buffers 與零拷貝證據

主來源：[shared_buffer_test.py](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/zero_copy/shared_buffer_test.py)、[zero_copy_benchmark.py](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/zero_copy/zero_copy_benchmark.py)、[common/add_chain.py](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/zero_copy/common/add_chain.py)。

- test:552–694 覆蓋 pooling、escaped torch/NumPy/DLPack/storage views；847–892 限制單 buffer 僅一種 NPU runtime 及 HIP→HSA 需配置時預告；946–960 覆蓋 close。這是測試程式覆蓋範圍，不是本次 pass 記錄。
- test:1135–1255 的 HSA 真實 dispatch 檢查要求結果與 counter，1222 的 `(3,0)` 及1247 的 `(2,1)` 明確區別 in-place 和 staged。其 `err < 20.0` 是此 routing 測試容差，不是 LLM 精度保證。
- benchmark:203–250、347–378 明留 GPU stream fence，不能因 zero-copy 省略 producer completion。
- benchmark:8–56、253–439：同 runtime 的 copy/shared 最容易公平對照；XRT 是兩 adds 的單 stitched ELF，HSA 是兩 launches，且 static operand staging 策略不同。不能把跨 runtime 總時間差全歸因於 shared memory。
- add_chain:72–84 註解說單 op multi-launch 重複執行有已知問題，採兩 op 避開；僅記為上游註解，未重現、未修復，文章未擴張成所有單 kernel 都失敗。
- exit 77 是缺環境／runtime 而 skip，不是 pass。Mapping 存在、數值相同、裝置原地執行三件事分別需要證據。
- Shared DRAM != pointer interoperability；可見性、順序及 lifetime 為正文必要條件。未提供通用裸指標轉交技巧，也未建議本機 ROCm preload／替換。

## Dashboard、legacy signedness 與指令宣稱

- [generate_readme.py:187–239](https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/examples/generate_readme.py#L187-L239) 勾號完全來自 transform 檔 `.exists()`；`--verify` 是 registry 完整性檢查，不是 NPU kernel 測試。
- [AIEVecToLLVM.cpp:4849–5048](https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/lib/Conversion/AIEVecToLLVM/AIEVecToLLVM.cpp#L4849-L5048)：舊式直接 `aievec.matmul_aie2p` pattern 的 i16 8×2×8 branch 回傳 conf=24，rewrite 沿用。i8 分支則明確合入 sign bits。
- [Peano aie2p_vmult.h:15–22](https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/clang/lib/Headers/aie2p/aie2p_vmult.h#L15-L22) 證明 signX/Y 在 bit9/8；24 不含兩者，雙 signed 對應 792。**狀態是靜態 signedness 風險、尚未動態重現**，不是整數硬體不支援，也不宣稱所有現代 AIR／IRON lowering 都會走這條 legacy pattern。cpp:5854 仍註冊該 conversion，不能把 legacy 誤寫為已移除。
- 不從 BF16/f32 tensor 型別、API 或 pack 形狀推導 machine instruction 數、原生 f32 multiply、INT4 吞吐或通用 SOTA。AIE2P 與其他架構能力不混用。

## 命令錨定與靜態驗證

- IRON vector_scalar_add 命令：設計檔本身及 `python/utils/hostruntime/argparse.py:22,67–86` 查核 `--dev npu2 --emit-mlir`。
- whole_array 命令：`programming_examples/basic/matrix_multiplication/whole_array/whole_array.py:442–524` 查核大小形狀、8 cols、bf16/f32、use-chess=0；仍需可用分區，未執行。
- Triton matmul 命令：固定 README 與相同目錄的 `.py`／`transform_aie2p.mlir` 查核。程式:91–94 有 M/N/K 尺寸掃描，非一次64×64。程式:85 的容差未擴張為一般模型門檻。
- Qwen 命令：CLI:349–443 查核 model/backend/max-tokens/profile，明註若執行可能下載權重，本次不做。
- JSON parse、精確七 slug、category/status、七個二級段落、無 H1、已知 related/internal slugs、四個以上 primary files／page 及 immutable commit URL 由本地 Python 靜態檢查；沒有匯入來源程式、呼叫網站 builder 或執行硬體測試。
- 每篇正文漢字（排除 in-body 外部引文連結）約 1,370–1,430 字，落在 1,200–2,500 範圍；每篇均有表格、來源錨定片段／命令或具體案例。URL 字元不列入中文篇幅。

最終本地靜態檢查結果（PASS；不代表 compiler／NPU tests）：

| slug | 二級段落 | 排除外部引文後漢字 | 不重複 primary files |
|---|---:|---:|---:|
| compiler | 7 | 1382 | 8 |
| iron | 7 | 1377 | 7 |
| triton | 7 | 1389 | 10 |
| runtime | 7 | 1373 | 8 |
| llm-graph | 7 | 1407 | 8 |
| qwen-case | 7 | 1374 | 8 |
| debug | 7 | 1427 | 14 |

另驗證 JSON 欄位集合、七個精確 slug／分類／status、balanced code fences、無 H1／script、related 與內文連結均屬 WIKI-PLAN 已知 slug、所有 source URL 使用40位 commit、所指本機 primary file 存在、line anchor 不超出檔案，以及 source entries 均在正文引用。第一輪嚴格 H1 字串檢查遇到 Python 區塊內的 `# ` 註解；已改為不帶空格的合法 Python 註解，重新檢查全數通過。未執行 site build 或整合／瀏覽器測試。
