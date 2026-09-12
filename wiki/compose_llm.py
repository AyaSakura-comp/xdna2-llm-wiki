"""Editorial data source for parent-authored LLM chapters; outputs content/llm.json."""
import json
from pathlib import Path
BASE='https://github.com/amd/Triton-XDNA/blob/5c33df1263f29de30f71616780c2e8a88e623782/'
AIE='https://github.com/Xilinx/mlir-aie/blob/0ed8e7e477fd9094acee8dada7ab81604a7fb07a/'
API='https://github.com/Xilinx/aie_api/blob/bec000fd312b407c61f25ef86fd582042e42d28a/'
S={
 'peano':('Peano README：外露管線 VLIW','https://github.com/Xilinx/llvm-aie/blob/386ca5c6634a84bb224b7248e79df8edabf0722f/README.md#L29-L45','固定 SHA；編譯器安排指令相依與暫存器讀寫時點，不是 lock／stream 等資料流等待的說明。'),
 'qwen':('Qwen2.5 model.py',BASE+'examples/qwen2_5/model.py','固定 source snapshot；裝置分支必須以實際程式為準，未在本機執行。'),
 'qwenread':('Qwen2.5 README',BASE+'examples/qwen2_5/README.md','部分敘述與 routing table 有差異，須交叉閱讀 model.py。'),
 'triton':('Triton-XDNA README',BASE+'README.md','實驗性 compiler；上游效能數字不代表本機量測。'),
 'whole':('IRON whole-array GEMM',AIE+'programming_examples/basic/matrix_multiplication/whole_array/whole_array.py','固定 SHA 範例；參數、packing、partition 須一起檢查。'),
 'linalg':('IRON linalg kernel geometry',AIE+'python/iron/kernels/linalg.py','dtype / mac_dims 與 kernel 路徑，非 API shape 全集。'),
 'memory':('Core data memory guide',AIE+'programming_guide/core_data_memory.md','SRAM 配置、bank 與 linker context。'),
 'devices':('NPU device models',AIE+'docs/Devices.md','裝置型號與 partition 描述，不能直接推出效能。'),
 'bf16':('AIE2P BF16 MMUL helper',API+'include/aie_api/detail/aie2p/mmul_bf16_bf16.hpp','macro 與 specialization 決定 emulation 路徑。'),
 'flash':('FlashAttention paper v2','https://arxiv.org/abs/2205.14135v2','GPU IO-aware 演算法論文，不是 XDNA2 kernel 的可用性證明。'),
 'gqa':('GQA paper v3','https://arxiv.org/abs/2305.13245v3','query / KV heads 分組與品質權衡。'),
 'awq':('AWQ paper v6','https://arxiv.org/abs/2306.00978v6','weight-only quantization 與平台感知 packing；GPU 結果不能移植成 NPU 吞吐。'),
 'paged':('PagedAttention paper v1','https://arxiv.org/abs/2309.06180v1','分頁與共享的系統概念，不是本 wiki 已實作的 runtime。'),
 'flm':('FastFlowLM README 固定快照','https://github.com/ROCm/FastFlowLM/blob/089e56d29416990e168abed43aff88fc0ad664f3/README.md','固定 SHA；README 的商用敘述與同版 TERMS.md 不一致，不能當成無條件商用授權。'),
 'flmterms':('FastFlowLM proprietary binary 條款','https://github.com/ROCm/FastFlowLM/blob/089e56d29416990e168abed43aff88fc0ad664f3/TERMS.md','同版條款列公司年營收 USD 10 million 門檻，與 README 免費任何商用的敘述有衝突；部署前須向權利人確認。'),
 'flmlin':('FastFlowLM Linux 安裝指南','https://fastflowlm.com/docs/install_lin/','外部可變來源；2026-09-12 查閱。需求專屬於此 runtime，不是所有 IRON 版本的要求。'),
 'lemon':('Lemonade Linux NPU guide','https://lemonade-server.ai/flm_npu_linux.html','外部可變來源；2026-09-12 查閱，未執行安裝。'),
 'amd':('AMD XDNA architecture','https://www.amd.com/en/technologies/xdna.html','廠商公共架構介紹，包含不同世代內容，不能視為完整 AIE2P ISA 規格。'),
}
articles=[]
def add(slug,title,summary,category,tags,body,refs,related,status='工程推導'):
 for key,(_,url,_) in S.items():body=body.replace('@'+key+'@',url)
 articles.append(dict(slug=slug,title=title,summary=summary,category=category,tags=tags,status=status,body=body.strip(),sources=[dict(label=S[k][0],url=S[k][1],note=S[k][2]) for k in refs],related=related))

add('gemm','GEMM：把矩陣切成可搬、可算的工作','從 Transformer projection 的 M/K/N，到 array、L1 與 microtile 的四層 tiling；算術多不代表 DMA 與同步便宜。','LLM推論',['GEMM','tiling','packing','projection'],r'''
## 先把 LLM 張量翻成 GEMM

線性層可寫成 `Y = XW`。把 batch 與這次處理的 token 數合成 M，輸入 hidden dimension 是 K，輸出 dimension 是 N。權重是否已轉置、stride 與連續性要明列；公式中的 B 是邏輯 K×N，不保證檔案中的權重也是這個排列。Prefill 的 M 通常較大，單序列 decode 的 M 通常為 1；後者接近 GEMV，不能直接套用大 GEMM 的效率。[Qwen model source](@qwen@) 可用來對照真實 projection 呼叫。

以下是數學工作模型，不是時間預測：dense GEMM 約 `2MKN` operations，採乘法與加法各算一次。bias、activation、padding、重排、低精度轉換不在這個數字裡。

## 四層 tiling 各自回答不同問題

| 層級 | 分割目的 | 常見錯誤 |
|---|---|---|
| Host 矩陣 M/K/N | 決定 tensor layout 與呼叫大小 | 把 batch 和 head 混進錯的維度 |
| Array rows/columns | 不同 core 負責不同輸出區塊 | 以為任意欄數都能取得 partition |
| Compute tile m/k/n | SRAM、buffer 深度、K 累加 | 只看 A/B，忘記 C 與 stack |
| Microtile r/s/t | 符合 kernel operand layout | 把 API call 當單一硬體指令 |

[whole_array.py](@whole@) 描述上述層級如何串起；[linalg.py](@linalg@) 提供選定 kernel geometry。兩者都要看，不能只改最底層 template。

## 一個容量推導例子

假設 BF16 A/B、FP32 C，m=64、k=64、n=32；A/B 各雙緩衝，C 單緩衝，另留 1 KiB stack：

```text
A = 64 × 64 × 2 = 8192 bytes
B = 64 × 32 × 2 = 4096 bytes
C = 64 × 32 × 4 = 8192 bytes
budget = 2 × (8192 + 4096) + 8192 + 1024
       = 33792 bytes = 33 KiB
```

這只是算式結果，**不是保證可編譯的 tile**。實際還有 globals、對齊、FIFO 展開、額外 accumulators、spill 與 bank placement。可回原始指南使用 L1 估算器；SRAM 真實限制讀 [core_data_memory](@memory@)。

## Packing 與重用先於更多核心

CPU row-major 的 64×64 block 不一定等於連續 `(r,s)` microtiles。優先讓 host 或 MemTile DMA 產生 kernel 要的 stream order，降低 core shuffle 和 scatter/gather 的負擔。但「DMA 能做重排」不代表任意高維 layout 都是一個合法 BD；維度數、stride、長度、對齊與元素單位都要查。

A 沿輸出 N 重用，B 沿輸出 M 重用。廣播若增加 route、同步或 BD 壓力，可能抵消節省的 DRAM 流量。K 分段時，C 的生命週期應跨 K chunks；若每塊都把 C 回寫再讀取，就要把額外 traffic 算回 roofline。

## Padding、尾端與數值路径

當 N、K 不整除 tile 時，可使用支援的 mask 或 zero-padding，最後裁回有效輸出。不要把 padded operation count 除以原始工作量當成更高 TOPS。對 BF16/BFP16，padding 還要維持 exponent block、轉置與 rounding 模式正確；改成 BFP kernel 並非只換一個 dtype 名稱。[BF16 helper](@bf16@) 說明 macro 會改变路徑。

## 實驗次序

先選一個合法小尺寸，對 CPU reference 檢查負值、outlier 與不整除尾端，再量單核、單欄、多欄。記錄 useful ops 和實際 padded ops、core time 和端到端 time。每次只變一個因素：tile、buffer 深度、placement 或 packing。若下界已由 memory 限制，先改善重用，不要先用更高宣傳 TOPS 解釋問題。
''',['whole','linalg','memory','bf16','qwen'],['mma','memory','dma','prefill-decode','performance'])

add('attention','Attention：算子可拆，不代表整體已能在 NPU 跑','把 QKᵀ、softmax、PV、causal mask 與線上歸一化分開看；FlashAttention 的 IO 思想不等於已有 AIE2P kernel。','LLM推論',['Attention','FlashAttention','softmax','GQA'],r'''
## Attention 的工作圖

對每個 batch 與 query head，簡化寫成 `O = softmax(QKᵀ / sqrt(d) + mask)V`。投影層 Q/K/V/O 是 GEMM，但投影之間還有 RoPE、head layout、mask、reduction 與 KV 更新。具備 BF16 GEMM 和 softmax 範例，只能證明元件存在，不能證明整個 attention graph 已映射、融合或端到端變快。[Qwen model](@qwen@) 是檢查實際裝置分配的入口。

## Prefill 與 decode 的 shape 不同

Prefill 對 S 個新 token 建立多行 queries；naive self-attention 的 score matrix 可達 S×S。Decode 每條序列只有一個新 query，卻要讀取已累積的 T 個 keys/values。前者往往面臨 score 中間值的 IO，後者更容易被 KV 讀取與派送延遲限制。是否採 chunked prefill、sliding window 或 prefix reuse 會改變 shape，必須把假設寫在 benchmark 旁。

## IO-aware tiling：不要保存完整 scores

[FlashAttention](@flash@) 的核心是以 SRAM tiles 計算並更新 softmax 統計，減少 GPU HBM 與 SRAM 之間的中間值存取。這是可借鑑的演算法，不是「XDNA2 已有 FlashAttention」的證據。映射到 NPU 還要回答：Q tile 放哪裡、K/V 從哪個 DMA channel 進來、row reduction 用哪些算術路徑、跨 tile 的 normalization 如何同步、partial output 是否留在 accumulator。

## 線上 softmax 的數學狀態

下面是每個 query row 的未正規化版本。m 是已看過的最大 score，l 是 exponential sum，U 是未除以 l 的 output；這是演算法示意，**不是可執行的 IRON kernel**。

```text
初值 m = -∞, l = 0, U = 0
對新的有效 score block S 與 Vblock：
  m_new = max(m, max(S))
  alpha = exp(m - m_new)
  P = exp(S - m_new)
  l_new = alpha*l + sum(P)
  U_new = alpha*U + P @ Vblock
  m,l,U = m_new,l_new,U_new
結束：O = U / l
```

若 block 全被 mask，需跳過或專門處理，不能直接讓 `-∞ - -∞` 產生 NaN。exp、除法與歸一化的精度要另行驗證；FP32 accumulator 不代表每個輸入乘法都是完整 FP32。與 reference 比較時必須對相同 causal offset、scale、RoPE 位置和有效 token 範圍。

## GQA 不只是把 heads 廣播

[GQA 論文](@gqa@) 區分 query heads Hq 與 KV heads Hkv。多個 query heads 共享一組 K/V，可減少 persistent KV payload。但若實作先把 K/V `repeat` 成 Hq heads 才送入 kernel，暫存和實際 traffic 可能回升。應檢查 expand 是否只是 view、是否 materialize，以及 kernel 是否原生使用 head-group 索引。

Qwen 範例 README 的部分舊 prose 與新 routing table 不一致；請讀 [案例頁](qwen-case.html) 的原始碼查核。這份 Wiki 不把 GPU-only fused kernel 冒稱為 NPU attention，也不把 CPU softmax fallback 當 NPU 成功。

## NPU attention 的驗證門檻

必須逐一證明 tail/mask 正確、長上下文穩定、cache append 正確、NPU dispatch 無 fallback、partial output 同步正確，以及完整 layer 比 baseline 更快。必要時先保留 attention 在 GPU，僅探索較大 projection 或 MLP 的 NPU 卸載；這是待測的分工方案，不是通用最佳策略。
''',['flash','gqa','qwen','qwenread','bf16'],['llm-graph','kv-cache','qwen-case','heterogeneous','validation'])

add('kv-cache','KV cache：容量、頻寬與生命週期','用 KV heads 而非 query heads 計算 payload；理解 GQA、cache append、分頁，以及「放得下」與「讀得夠快」的差別。','LLM推論',['KV cache','GQA','capacity','paging'],r'''
## Cache 保存什麼、不保存什麼

自回歸 decoder 保存各層已生成 tokens 的 keys 與 values，避免每一步重算所有過去投影。它通常不保存每一步完整 attention score matrix，也不是普通 CPU cache 的自動替換機制。配置、位置索引、append、重用、釋放都由模型/runtime 管理。[Qwen model.py](@qwen@) 有預先配置並原地寫入 KV 的具體例子。

## 先算理想 payload

若每層 KV shape 相同、所有序列長度都為 T、無 sliding window、無共享 prefix，則：

```text
KV bytes = 2 × B × L × Hkv × D × T × s
B = batch / 並行序列數
L = layers, Hkv = KV heads, D = 每 head 維度
T = 每序列保留 tokens, s = 每 KV 元素 bytes
2 = K 與 V 兩份
```

這是張量元素計數的推導，不是配置器的實測佔用。B=1、L=32、Hkv=8、D=128、T=8192、s=2 時，結果為 **1,073,741,824 bytes = 1 GiB**。每層尺寸不同則改用逐層加總；不同序列長度則按各序列有效或配置長度分別計算。

## GQA 與 MQA 如何省容量

MHA 常有 Hkv=Hq；MQA 的 Hkv=1；GQA 介於兩者之間。[GQA](@gqa@) 研究品質與效率的權衡。因此不能用 Q heads 代替 KV heads；也不能在模型未修改時任意減少 KV heads，因為那會改變模型架構與权重相容性。

若 query 分組讀取共享 K/V，理想可避免重複存儲。但若為滿足某 kernel layout 而把 cache 展開成完整 heads，應把 expanded buffer 另外計算；理論 GQA payload 不等於這個 backend 的真實 peak memory。

## Payload 之外的記憶體

| 項目 | 為什麼多出來 |
|---|---|
| Alignment / padding | Tile geometry、頁面與 vector 對齊 |
| Quantization metadata | scales、zero points、block headers |
| Runtime workspace | staging、packing、雙緩衝、暫存 output |
| Prefix / beam bookkeeping | page tables、索引與共享管理 |
| Peak activation | Prefill 或重排階段與 KV 同時存在 |

[核心 SRAM 文件](@memory@) 討論 tile 級容量；系統 DRAM 裡的完整 KV 不會因為 L1/L2 命名就自動被透明快取進 NPU。一次計算應只搬需要的 block，並清楚指定順序與 buffer 生命週期。

## Decode 的頻寬問題

假設每步需要讀一次全層已有 K/V，KV read traffic 會隨 T 成長；GQA 若重用不佳則可能讀更多。權重也需要讀取，因此「模型權重小了」不代表長 context 的 decode 一定快。NPU DMA、DRAM、GPU 與 CPU 可能競爭同一實體頻寬；不能給每個裝置各算一次完整峰值頻寬後再相加。

## 分頁與正確性

[PagedAttention](@paged@) 的 block 管理可減少 fragmentation、預留浪費與重複 prefix，但不會讓相同 K/V 數值的 payload 憑空消失。它也不保證 XDNA2 runtime 已有相同功能。要移植時，page table traversal、非連續地址、DMA BD 限制與 host 介入成本都需另外設計。

驗證 append 時要測 cache slot 只更新一次、query causal offset 正確、跨 page 邊界正確、不同序列彼此隔離、reset 不洩漏舊資料。下方計算器只處理理想容量；不推估本機可跑 context 上限或 tokens/s。
''',['qwen','gqa','memory','paged'],['attention','memory','prefill-decode','performance','validation'])

add('quantization','LLM 量化：格式、數學與 kernel 是三件事','W4A16、INT8、BF16、BFP16 與 GGUF/AWQ 不是可以任意互換的標籤；必須追到 unpack、scale 與真正的 multiply 路徑。','數值',['quantization','INT4','AWQ','BFP16'],r'''
## 先拆開五個層次

檔案格式描述 bytes 怎麼保存；量化方案描述如何近似數值；kernel layout 描述 SIMD/MMA 需要的排列；compiler lowering 選擇指令；runtime 決定資料在哪裡解包與運算。讀到 GGUF Q4 或 AWQ 4-bit，不能直接推出 AIE2P 有相同格式的 native MMA。[AWQ](@awq@) 本身就把平台感知 packing 與 kernel fusion 視為效能要素。

## W4A16 不等於 4×16 matrix primitive

W4A16 通常意指權重以低位元表示，activation 使用較高精度；真正計算可能是先反量化 W，再做 BF16 算術，也可能融合 unpack、scale 和累加。A/B 的順序、signedness、group size、zero point、scale dtype 會影響可用 implementation。僅看檔案中每個權重 4 bits，不足以用「4-bit TOPS」估算速度。

本次 Peano snapshot 的 INT8×INT4 4×16×16 wrapper 是 unpack + 兩次 INT8 primitives；這是該工具鏈的靜態路徑，不是「整顆 XDNA2 永遠沒有其他 INT4 能力」的證明。完整 immutable 展開見 [MMA 條目](mma.html) 與原始稽核。

## 常見 affine 量化的數學

```text
近似權重 w_hat = scale × (q - zero_point)
weight-only linear:
  y_j ≈ sum_k x_k × scale_group(k,j) × (q_kj - zero_group(k,j))
```

這是常見示意，不是所有 GGUF/AWQ 編碼的精確格式。scale 若每 group 改變，就不能毫無條件移到整個 K reduction 外。非對稱 zero point 也會帶來 correction term。要先寫清數學，再判斷可融合哪一段、用哪種 accumulator，以及輸出縮位在哪裡发生。

## BF16 與 BFP16 的風險不同

BF16 每個值有自己的 exponent；AIE2P BFP16 EBS8 的 block 共用 exponent，不能叫 IEEE FP16 或 FP8。對 outlier 強烈的 block，共享 exponent 會犧牲較小值精度。[AIE2P BF16 helper](@bf16@) 的 BFP emulation macro 會改變數值路徑，並不保證無損等價。

BFP packing 可能減少 operands 的 bytes，但若額外保留 BF16 原本張量、conversion buffer 與轉置副本，peak memory 未必下降。對 LLM 應分別評估 projection、attention normalization、residual 與 KV，不能只在隨機矩陣上過 tolerance 就宣告整個模型可靠。

## 一個 7B 權重容量的理想下界

假設全部 7×10⁹ 個參數都用固定 4 bits，裸 payload 是 `7e9 × 4 / 8 = 3.5e9 bytes`，約 3.26 GiB。這不是實際模型檔案大小：有 scales、block headers、某些保留高精度的 tensors、metadata 與 runtime workspace。也不代表 7B 模型在 NPU 上全部算子都有 kernel。

| 要比較 | 必須固定 |
|---|---|
| 誤差 | calibration、輸入範圍、rounding、accumulator |
| Kernel 速度 | 同形狀、同 packing、相同輸出精度與有效工作量 |
| 端到端品質 | tokenizer、prompt、採樣參數、模型版本 |
| 記憶體 | 權重 + KV + peak activations + 額外轉換副本 |

## 實作前的核對清單

列出每一個格式的 bit order、group 與 padding；用正負數、全零、飽和邊界、極大極小值驗證 dequant reference；再看 compiler IR 與 core disassembly 是否有意外 CPU fallback 或重複 conversion。先確定 [資料型別](datatypes.html) 和 [數值驗證](validation.html)，再談量化加速。AWQ 論文的 GPU speedup 不能轉抄為本機 XDNA2 實測。
''',['awq','bf16','linalg','triton'],['datatypes','mma','validation','kv-cache','deployment'])

add('prefill-decode','Prefill 與 decode：兩個不同的效能問題','Prefill 重視大矩陣吞吐與 TTFT；decode 重視逐 token 依賴、權重/KV 流量與派送延遲。','LLM推論',['prefill','decode','TTFT','TPOT'],r'''
## Prefill 的工作

Prefill 一次處理 prompt 中多個 token，建立各層 activation 與 KV cache。對線性層而言，M 可近似這次處理的 token 數乘 batch，較有機會重用同一權重區塊。這不代表所有 prefill 一定 compute-bound；短 prompt、padding、attention IO 或同步仍可能佔優。

## Decode 的工作

Autoregressive decode 需要前一個 token 的輸出才能選下一個輸入；單條序列的大部分線性層變成小 M。若 batch=1、沒有其他重用，每一步可能重新讀大量權重，並讀取累積 KV。把 decode 的 kernel 換到另一個装置，需要額外付出 buffer 可見性、dispatch 與 graph 切換成本。[Qwen backend modes](@qwenread@) 是不同階段採不同裝置分工的具體範例。

## 正確拆分指標

| 指標 | 建議定義 | 不應混入的宣稱 |
|---|---|---|
| TTFT | 從明確請求邊界到第一 token 可用 | 不應用一次預先編譯 kernel 時間代替 |
| Prefill latency | 固定 prompt 工作的前向時間 | 不等於整段聊天延遲 |
| TPOT | 後續 tokens 的平均或分位間隔 | batch throughput 不等於單用戶延遲 |
| Decode throughput | 固定生成 token 数 / 對應時間 | 不要把 prompt tokens 加進分子 |
| Cold vs warm | 是否含編譯、配置、載入與映射 | 冷暖結果不可直接交叉比較 |

開始/結束時間邊界要同步裝置；只量非同步 enqueue 是派送開銷，不是完成時間。這些是本 Wiki 的量測定義建议，非上游硬體規格。

## 小 M 為什麼可能吃不滿 matrix engine

GEMM 的理想最少流量約 `(MK+KN)s_in + MN*s_out`。當 M=1，權重 KN 通常壓倒其他項，算術強度接近 `2/s_in` ops/byte；若 BF16 權重佔 2 bytes，就是接近 1 ops/byte 的簡化上界。忽略了 cache 與量化時，增加算術峰值往往無法消除頻寬限制。詳見 [效能模型](performance.html)。

硬體 matrix primitive 有固定 M/K/N geometry。把 M=1 補到8或更大，增加的是實際運算與搬運，不是有用 tokens。Compiler 能否 specialize 小 M、合併不同序列、減少 launch，要逐項驗證。

## Chunked prefill、batch 與推測解碼

Chunked prefill 把長 prompt 分塊，可能改善與 decode 請求間的排程公平性，但也改變 DMA、cache indexing 和單次 GEMM M。Continuous batching 把多條序列合在一起，提高 M 與重用，代價是更複雜的動態 shapes 與 KV 管理。[PagedAttention](@paged@) 是理解 serving 記憶體系統的參考，不是本 runtime 的現成功能保證。

Speculative decoding 可把部分驗證工作變成多 token forward，但接受率、draft 成本、資料搬運與採樣正確性都要計入。不能把 GPU MTP 的已知加速比直接套到 XDNA2；本 Wiki 沒有實作或測量 NPU speculative decoding。

## 試驗怎麼設計

至少測短/中/長 prompt、短/長 cache 與不同 batch；固定模型、權重dtype、prompt、輸出 token 數及採樣策略。分列 per-op time、copy/map/sync、fallback 次數、TTFT、TPOT 與記憶體峰值。若 hetero-fast prefill 使用 NPU、decode 回 GPU，應如實標示兩段路徑，而不是稱整段生成均由 NPU 加速。[Qwen model.py](@qwen@) 是核對 dispatch 的最終入口。
''',['qwen','qwenread','paged','whole'],['gemm','kv-cache','heterogeneous','performance','qwen-case'])

add('heterogeneous','CPU × GPU × NPU：分工與資料所有權','Shared DRAM 不代表免費互通；卸載是否值得，取決於計算節省是否大於映射、同步、轉換與 fallback 的成本。','LLM推論',['heterogeneous','zero-copy','shared memory','synchronization'],r'''
## 三個裝置不是同一個 execution target

Strix Halo 的 CPU、gfx1151 GPU 與 AIE2P NPU 可以共享系統記憶體資源，但各自有不同的程式模型、指令、runtime 與完成通知。HIP binary 不能直接交給 NPU；能在 CPU 看到同一 virtual address 也不代表對所有裝置都是可用的 handle。[Triton-XDNA README](@triton@) 對 XRT、HSA 與 shared buffers 分別規範。

## 一個最小卸載成本模型

假設一段 GPU 工作耗時 t_gpu；改到 NPU 的完整替代成本為：

```text
t_replace = t_export_or_map + t_convert + t_npu
          + t_sync + t_import_or_consume + t_fallback
只有 t_replace < t_gpu 才可能單段受益
```

這是無重疊的簡化估算。真正 pipeline 需分析 critical path，不能把可重疊成本與不可重疊成本一律相加或一律忽略。若 NPU 讓 GPU 同時做其他有效工作，還要比較整個 graph 的 makespan，而非局部算子速度。

## Shared buffer 要回答四個問題

1. **位址與映射**：配置者是誰，哪個 runtime 提供每個裝置的 handle？
2. **可見性與順序**：producer 完成後，consumer 如何等待並看見最新資料？
3. **生命週期**：所有裝置完成前不能回收、重用或解除映射。
4. **表示法**：相同 pages 上的 layout、dtype、padding 是否適合兩邊？

Zero-copy 通常意指避免一份 tensor 的 staging copy，不表示沒有 DMA、DRAM traffic、cache maintenance、映射成本或同步。以 `shared` API 的 dispatch 計數確認 in-place / staged，再量端到端；不要只看函式名有 zero_copy 就當作達成。

## XRT 與 HSA 的邊界

固定版本 README 提到兩種 NPU runtime 與對應 artifacts；HSA 路徑需要 AIE-capable ROCR，不能因為已安裝可跑 gfx1151 的 ROCm 就推論也能派送 AIE kernel。PyTorch 可能先載入另一份 libhsa-runtime，造成同 process ABI/功能不匹配。這是應在隔離環境裡查核的相容性問題，**不是本 Wiki 要求你修改現有 GPU 服務**。[runtime 條目](runtime.html) 有更完整的核對方式。

## 算子放在哪裡：先當假說

| 工作 | 合理的待測候選 | 為何不能預先下結論 |
|---|---|---|
| 大 MLP / projection | NPU dense matmul | padding、dispatch、共享頻寬可能抵消 |
| Fused attention | 現有 GPU kernel | NPU mapping 是否完整需另外驗證 |
| Tiny decode op | GPU 保留或融合 | 跨裝置一次 round trip 可能更貴 |
| Tokenization / sampling | Host 控制 | CPU 工作不是「全 NPU」宣稱中可忽略的部分 |

[Qwen 範例](@qwen@) 的 npu / hetero / hetero-fast 是具體 routing choices，不是各 workload 的最佳性證明。NPU 模式內仍有 CPU 工作；hetero-fast decode 回到 GPU。把模式名稱和實際 per-op 執行分開記錄。

## 共享 DRAM 的競爭與測量

同時跑 GPU 和 NPU 可能競爭 DRAM 與功耗預算，不應把兩邊獨立跑的 bandwidth 或 peak 算力直接相加。需量相同整體 workload 的 latency、energy、device residency、fallback 與記憶體峰值。改善圖分割時，優先合併相鄰子圖、延長 buffer 重用生命週期，避免每一個小 op 都跨裝置往返。
''',['triton','qwen','devices','memory'],['runtime','synchronization','prefill-decode','qwen-case','performance'])

add('deployment','LLM 部署生態：研究 compiler 與成品 runtime','IRON／Triton 適合研究 kernel，FastFlowLM／Lemonade 著重模型部署；「可免費用」與「所有核心原始碼公開」必須分開。','程式設計',['FastFlowLM','Lemonade','deployment','license'],r'''
## 先分清你要改哪一層

若要研究 MMA 展開、DMA placement 或自訂算子，從 [IRON](iron.html)、[Triton](triton.html) 與 Peano 看得最清楚。若目標是用已支援模型提供本地推論服務，模型 runtime 和 serving 介面才是主要入口。這兩條路可以共享部分底層技術，但不代表相同公開範圍或同一套 binary ABI。

## 部署路線圖

| 路線 | 適合目的 | 必須確認 |
|---|---|---|
| IRON / MLIR-AIE / Peano | 學習與自訂 dataflow / kernels | 相符 source、wheel、driver 與 runtime |
| Triton-XDNA / AIR | compiler-generated kernels / 研究性 LLM graph | transform、fallback、per-op routing |
| FastFlowLM | 已支援 LLM / multimodal 模型部署 | model list、kernel binary、runtime 版本與 license |
| Lemonade + FLM | 管理模型與 API 使用體驗 | 實際 backend、請求參數、log 與 NPU 驗證 |

[FastFlowLM 官方 repository](@flm@) 明列 XDNA2 家族支援與 CLI/模型下載流程；[Lemonade 指南](@lemon@) 說明 Linux NPU 整合。這些是上游文件陳述，本機沒有安裝或 benchmark。

## 開源範圍不能只看 repository badge

FLM 的 README 區分 MIT orchestration / CLI 與 NPU-accelerated binary kernels；binary kernels 不等於所有 source 與重建流程公開。**同版文件另有實際授權矛盾**：README 說 kernels 免費供任何用途（含商用），但 [TERMS.md](@flmterms@) 明列 proprietary binaries，且對公司年營收超過 USD 10 million 的商用要求另外授權。這份 Wiki 不能裁決哪個文字是最新有效授權，亦不提供「無條件免費商用」保證。商業部署前須向權利人確認，保留採用版本與授權文件；不能只看 README 或 MIT badge。

同樣地，compiler 是開源不代表 BIOS、firmware、所有驅動包與模型授權都開源。第三方量化模型還有其自身 license，應列入 deployment manifest。

## Linux 需求是 runtime-specific

[FLM Linux 指南](@flmlin@) 與 [Lemonade Linux NPU 指南](@lemon@) 在查閱快照中列出 firmware 1.1.0.0+、kernel 7.0+ 配合 amdxdna 或相應 DKMS 路線，以及 memlock 條件。這不代表先前 IRON 的每個版本也要求同一組版本；不同文章可能對不同發行版、backport 與 firmware 協定作假設。

不要依一篇 gist 直接改 BIOS、替換 kernel、覆蓋 ROCm 或放寬全系統 limits。先核對自己的 SKU、發行版、既有 GPU 工作、driver path 與 rollback 計畫；系統修改應是另一次明確授權的任務。

## Validation 通過還不代表模型能執行

官方指南指出 `flm validate` 與實際 `flm run` 所走的檢查路徑不同：前者可能確認 kernel DRM 裝置，而執行還需要 XRT 能看到裝置。因此驗證成功但模型啟動失敗時，還要看 `xrt-smi examine`、plugin 與 runtime log。沒有在這裡執行上述命令；它們是依官方文件列出的查核入口。

對服務化 LLM，另外記錄真正的 backend、模型 artifact、context 配置、tokenizer/chat template、冷暖狀態與 resource limits。生成文字成功不是無 fallback 的證明；NPU utilization 閃一下也不是端到端所有算子都在 NPU 的證明。

## 不移植宣傳效能

官方 README 的功耗效率、最大 context 與安裝時間陳述有自己的測試條件，不能用來推估這台主機的 TPOT。社群「CPU/GPU 幾乎零負載」也不能當硬體事實。請依 [驗證流程](validation.html) 收集 per-op 路徑與完整 latency，再決定研究 compiler 或成品 runtime 是否符合需求。
''',['flm','flmterms','flmlin','lemon','triton'],['compiler','runtime','qwen-case','validation','sources'],'來源查核 + 部署界線')

add('performance','效能模型：容量、Roofline 與端到端下界','用可驗算的公式排除不合理期待，再用量測找瓶頸；計算器預設值不是本機 XDNA2 規格。','驗證與知識庫',['roofline','bandwidth','TOPS','latency'],r'''
## 先問是哪一種限制

容量不足、傳輸不足、算術不足、同步太多與 runtime 太慢是不同問題。容量回答「能放哪裡」；bandwidth 回答「能搬多快」；compute throughput 回答「可執行多少有效運算」；launch/依賴決定小工作是否有用。這些層級不能用一個 TOPS 數字取代。[IRON GEMM](@whole@) 同時含 tile、DMA 與 host 控制，正好說明為什麼要分開測。

## GEMM 的理想工作與最少流量

採 dense `C=A×B`、β=0、不讀舊 C、A/B 各讀一次、C 寫一次的理想模型：

```text
Ops = 2 × M × K × N
Bytes_min = (M×K + K×N) × input_bytes + M×N × output_bytes
Arithmetic intensity = Ops / Bytes_min
```

這裡的一次讀取是理想重用條件，不是實際 NPU DMA 的保證。多次搬運 C、padding、packing、metadata、權重解包或無法保留的 A/B 都會增加流量。對 FlashAttention 這类融合演算法，應用其真實中間值策略，不能把獨立 GEMM 下界直接加總當成完整 attention 下界。[FlashAttention](@flash@) 特別強調 IO 模型的重要性。

## 以同一精度定義算力與流量

```text
t_compute >= Ops / effective_ops_per_second
t_memory  >= Bytes_min / effective_bytes_per_second
t_kernel  >= max(t_compute, t_memory)     # 理想充分重疊
```

若計算輸入是 BF16/BFP，卻拿 INT8 的峰值當有效算力，模型已經不一致。BFP conversion、emulation 或低精度 decomposed multiplication 應依真正路徑估算，而不是一次 `mmul` 算一次 cycle。對未知的有效頻寬，不要冒用 DRAM pin rate 或 GPU benchmark 當 NPU實測。[數值型別](datatypes.html) 與 [MMA](mma.html) 先釐清算的是什麼。

## 下界不是 prediction

下方工具的 10 TOPS 和 50 GB/s 是使用者可調的教學假設；不是實測，也不是 XDNA2 任何 SKU 保證。所得最小時間是假设所有其他成本消失且重疊理想的樂觀值。實際時間可以高很多；若量測比下界更短，先查單位、有效工作量、計時同步與假設是否错。

TOPS 使用十進位 10¹² operations/s；GB/s 使用 10⁹ bytes/s；KiB/MiB/GiB 使用 2 的冪。把兩組單位混用會引入系統性差異。下方流量顯示 MiB，而使用者頻寬輸入是 GB/s，程式在計算時明確換算。

## 從單核到模型的量測階梯

1. 查單核 schedule、spills、loads 與數值誤差。
2. 在同樣資料與相同輸出格式下，測多核心、廣播與 buffer 深度。
3. 加入 host packing、配置與完成等待。
4. 放回 Transformer graph，檢查 conversion、fallback 與共享記憶體競爭。
5. 分別報 cold TTFT、warm TTFT、TPOT、batch throughput 與 peak memory。

不以最漂亮的一次值代表穩定結果。固定輸入、記錄分布、重跑基準；對溫度、功耗政策與併行背景工作保持透明。本 Wiki 不會從這些純數學工具產生虛構 tokens/s 排名。

## 值得優先做的改善

若 memory 下界佔優，先減少重讀、改善 layout、維持 buffer 重用或選合適量化；若 dispatch 佔優，融合相鄰工作或減少跨裝置邊界；若 compute 佔優，才進一步看 microtile 與指令排程。每個改善都須以完整正確性測試守住，不把降低 precision 的結果當免費優化。
''',['whole','flash','linalg','triton'],['gemm','prefill-decode','heterogeneous','validation','debug'])

add('validation','正確性與效能驗證：一套不把 fallback 當成功的流程','从 reference、數值誤差、dispatch 證據到完整 LLM quality；每一層只回答自己能證明的問題。','驗證與知識庫',['validation','fallback','benchmark','numerics'],r'''
## 五層通過，不可以跳級

| 層級 | 證據 | 仍未證明 |
|---|---|---|
| Source inspected | pinned headers / mapping / tests 已閱讀 | binary 可建置 |
| Compile | artifact 成功產生，target 正確 | 硬體成功執行 |
| Dispatch | device completion、正確 buffer／ABI | 結果數值正確 |
| Correctness | reference 與特定測資誤差通過 | 任意輸入、整個模型或效能達標 |
| End-to-end | 無未揭露 fallback，模型品質與時間可重現 | 其他 SKU、版本與 workloads 也一樣 |

這份 Wiki 主要位於第一層，加上數學和網站測試；沒有冒充後四層。Compiler dashboard 的 checkmark 可能只代表 transform file 可用，需以其圖例與實際測試紀錄為準。[Triton README](@triton@) 的「experimental」是重要範圍標示。

## 建立明確 reference

固定 shape、layout、signedness、input/output dtype、scale、rounding、saturation、accumulator 與 random seed。BF16×BF16→FP32 的 reference 應先量化輸入成相同 BF16，再累加比較；若 kernel 轉 BFP，應另有模擬同 block exponent 路徑的參考。不能用 FP32 全精度輸入的差異籠統判定所有誤差都是 compiler bug。

對 integer，至少包含負值、0、邊界與可能溢位的 K 長度；對 float，包含近零、outlier、不同量级與 mask。NaN/Inf 行為若不在規格承諾內也應明列，而不是悄悄排除。

## 指標不只一個 allclose

可同時報 max absolute error、相對誤差（分母需處理近零）、RMSE、cosine similarity，並報測資分布與 tolerance。單一 `allclose` 可能被少數大值或寬鬆門檻掩蓋。對模型還要比較 logits、top-k、固定採樣輸出與任務品質；字串一致性不是唯一品質指標，字串不一致也不自動代表全部數值錯誤。

[AIE2P BF16 helper](@bf16@) 與 [IRON kernel geometry](@linalg@) 是決定精度路徑的來源；設定檔與編譯 macro 必須保存。

## 揪出靜默 fallback

很多研究性範例在 NPU compilation 失敗時會回到 PyTorch。這對 demo 友善，對 benchmark 卻危險。應保存每個 op 的實際 backend、首次編譯結果、dispatch counters 與 fallback log；測量模式最好在 fallback 時顯式 fail 或至少獨立標示其耗時。[Qwen model](@qwen@) 與各 kernel wrappers 要一起讀。

CPU 的 embedding、sampling、attention core 或 LM head 若是設計選擇，應稱為 CPU+NPU 路徑，不必假装是意外 fallback；但是 mode 名叫 npu 並不能掩蓋它們。

## 端到端計時邊界

測時間前明確完成事件或 device synchronize，防止只量 enqueue。分開編譯、權重載入、配置、host packing、mapping、transfer、compute、等待與輸出後處理。比較同一筆 useful work 和同品質設定；不要一邊含下載或JIT，另一邊已warm cache。

把結果寫成 manifest：source SHA、工具鏈版本、driver/runtime、SKU/partition、shape、dtype、seed、容忍誤差、cold/warm、背景負載與artifact hash。相同 inputs 不保證相同硬體狀態，應記錄多次分布而非只報最好一次。

## 可直接使用的驗證紀錄模板

```text
Claim: 這個 op 在 AIE2P 上無 fallback 執行
Source / artifact hash:
Device / partition / driver / runtime:
Input shape / dtype / layout / seed:
Compiler flags / macros / padding:
Reference arithmetic and tolerance:
NPU dispatch evidence / fallback count:
Max error / model quality:
Warmup policy / repetitions / timing boundaries:
Result / unresolved gaps:
```

先以一條可以被否證的 claim 開始；遇到失敗先保存最小重現與 logs，再回 [debug](debug.html) 查根因，而不是不停增加 tolerance 或換測資讓它過。
''',['qwen','triton','bf16','linalg'],['debug','performance','quantization','qwen-case','wiki-method'])

add('glossary','術語辭典：同一個字，在不同層可能不同意思','快速對照 XDNA2、AIE2P、tile、buffer、MMA、BF16/BFP16 與 LLM 推論常用語，並連回完整條目。','驗證與知識庫',['glossary','術語','definitions'],r'''
## 裝置與架構

| 術語 | 本 Wiki 的意思 | 延伸 |
|---|---|---|
| XDNA 2 | Ryzen AI 平台的一代 NPU 架構 | [系統](system.html) |
| AIE2P / arch21 | 本次 source 查核的 XDNA2 core target | [ISA](isa.html) |
| AIE2PS / arch22 | 不同 target，不能移植其 FP8/FP16 支援結論 | [資料型別](datatypes.html) |
| gfx1151 | Strix Halo iGPU 的 ROCm GPU target，不是 NPU | [分工](heterogeneous.html) |
| NPU2 | MLIR-AIE device model 家族名稱 | [系統](system.html) |
| Partition | Runtime 分配的 array 區域，不一定等於整顆硬體 | [runtime](runtime.html) |

架構命名依 [Devices.md](@devices@) 與固定版本 backend；勿把 API 文件中所有世代的同名型別合併成一張 XDNA2 能力表。

## Tile、記憶體與資料流

| 術語 | 重點 |
|---|---|
| Compute tile | 執行本地 scalar/vector 程式，搭配 data/program memory |
| Memory tile / MemTile | staging、重排、分配資料，不是透明一般 CPU L2 cache |
| Shim tile | Host 與 array 的資料入口/出口與相關連接 |
| Scratchpad | 軟體顯式管理的 SRAM，不是硬體自動替換cache |
| Bank | 影響存取衝突與配置的記憶體分區，不能僅靠總容量判斷速度 |
| DMA / BD | 搬運引擎與其 buffer descriptor；descriptor 不是資料本身 |
| ObjectFifo | 編譯器可 lowering 的資料生命週期抽象，不是 Python queue 在 NPU 裡跑 |
| Lock / token | 協調可用資料與可用空間，錯誤 acquire 順序會阻塞 |
| Cascade | 傳遞特定資料／部分累加值的專用路徑；可用性與例子需分開查 |

更多細節見 [記憶體](memory.html)、[DMA](dma.html)、[同步](synchronization.html)；精確數量與地址不可只從這張辭典推導。[core_data_memory](@memory@) 是 SRAM 的原始閱讀入口。

## 算术與格式

| 術語 | 容易混淆之處 |
|---|---|
| SIMD | 多 lanes 執行相同類別向量計算；不等於 GPU warp |
| VLIW | Compiler 將多種操作排入 instruction bundle；AIE2P 的外露管線由編譯器安排指令相依與讀寫時點，不靠一般指令相依性 stall 邏輯；lock／stream 等資料流等待是另一層問題。見 [Peano README](@peano@)。 |
| MMA / MAC | 矩陣或向量乘加；API call 可能展開多條 primitives |
| Accumulator | 中間累加表示，寬度不是輸出dtype |
| BF16 | 每個元素具有自己的 exponent |
| BFP16 | Block floating point，共享 exponent；不是 BF16/IEEE FP16 |
| EBS | Exponent block size，不是單個數值的 bit width |
| Packing | 把資料排成 kernel operand layout，可能包含轉置與量化封装 |
| Emulation | 以其他算術路徑合成；成本與精度要看實作 |

[BF16 helper](@bf16@) 顯示 macro/specialization 對實作的影響。看「支援」時要問：可表示、可搬運、可做單一primitive、API有組合，還是 frontend已有測試？

## Compiler 與 runtime

IRON 是 Python dataflow programming 入口；MLIR-AIE 是 array 配置與 lowering 基礎；Peano 是 LLVM-AIE core backend；Triton-XDNA 把高階 kernel 經 triton-shared、Transform、AIR 與 AIE stack 降到裝置。[compiler](compiler.html) 串起各層。

XRT 與 HSA 是不同 runtime 路徑；ELF、xclbin、PDI、instruction stream 是不同 artifact，不能只按副檔名交換。Zero-copy 是避免特定 staging copy，不是零交通、零同步或零映射。Fallback 是改由其他 backend 執行；編譯器成功 return 不一定代表所有工作真的在 NPU。

## LLM 與量測

Prefill 處理 prompt 並建立 cache；decode 依賴上一 token 逐步生成；KV cache 保存 keys/values；GQA 共享較少的 KV heads。[GQA 論文](@gqa@) 是 query/KV分組的來源。TTFT 是到第一 token 的延遲；TPOT 是後續 token 間隔；tokens/s 可是 batch aggregate 或單序列，必須寫清。

Roofline 用 arithmetic intensity 連接頻寬與算力上界；本 Wiki 工具顯示的是理想時間下界，不是硬體實測。KiB/MiB/GiB 用2的冪，GB/s和TOPS用10的冪。「固定source快照」表示版本可追溯，不代表相互相容可建置的 dependency lock。
''',['devices','memory','bf16','gqa','triton','peano'],['system','datatypes','compiler','llm-graph','wiki-method'],'術語整理')

add('sources','來源地圖、證據等級與未解問題','主張要能回到原始文件與固定 source；公共架構介紹、API 表、compiler 實作和 benchmark 各有不同證明力。','驗證與知識庫',['sources','evidence','provenance','limitations'],r'''
## 這份 Wiki 能做到的完整性

這是依公共文件、下載 source snapshots 與演算法文獻整理的廣泛技術知識庫，不是 AMD 保密設計文件或逐一列出所有 opcode 的正式 ISA 手冊。沒有公開或沒有查核的 latency、bus width、clock、firmware 排程與全部 SKU差異會留白；不以「完整」之名補猜測。

每頁提供來源與 related/backlinks；首頁可下载 source-register.json，列出唯一 URL 與引用條目。knowledge.json 保留結構化內容，Markdown 與 llms-full.txt 保留來源文字和界線。另可直接開啟 [原始 manifest](research-manifest.json)、[型別／MMA 稽核](type-mma-audit.md)、[原始長篇指南](guide/index.html)。

## 證據分層

| 等級 | 能支持什麼 | 不可替代 |
|---|---|---|
| 廠商公開架構文件 | 大方向、產品級設計與其限定規格 | 每個compiler實際lowering |
| 固定source/header | 這個版本的型別、primitive wrapper、配置與分支 | silicon實測或所有版本行為 |
| 上游測試/範例 | 預定支援範圍與驗證方法 | 本機重現；存在文件不等於測試已pass |
| 論文 | 演算法與論文條件下的結果 | 自動移植到XDNA2的加速比 |
| 工程推導 | 由明確假設推導的容量/成本 | 實際配置器大小或throughput |
| 本機量測 | 若真的執行才可如此標記 | 本Wiki尚無NPU量測 |

[AMD XDNA 公共頁](@amd@) 同時談不同世代，引用時須切分範圍。多個 AMD/Xilinx repositories 互相一致可提高解讀把握，仍不是三份獨立 silicon validation。

## 固定快照與可變文件

MLIR-AIE、Peano、AIR、Triton-XDNA、AIE API 與 IREE-AMDAIE 的 SHA 可在原始 manifest 找到。這些 snapshot 是分別取得，**未驗證組成同一套可建置工具鏈**。LLVM-AIE 是指定範圍的 sparse checkout，不是完整離線 LLVM bundle。

新增的 FLM/Lemonade 官方網站與論文頁以查閱日期和版本標記；動態安裝需求應部署前再核對。[FLM Linux](@flmlin@) 和 IRON guide 可能針對不同runtime/firmware協定，不能選一個版本號就當整個XDNA2平台的唯一要求。

## 已發現的矛盾

- AIE API 模式名不一定代表一條 native matrix instruction；INT4 wrapper 可展開成 INT8，BF16 helper 可展開成多次向量原語。
- AIE2P arch21 與 AIE2PS arch22 的 FP16/FP8 型別不能混用。
- [Qwen README](@qwenread@) 的舊 prose 與新 routing table 有不同裝置描述；[model.py](@qwen@) 的分支是本版本查核的優先依據。
- [FLM官方README](@flm@) 區分 CLI/orchestration 與 binary kernels；它的「任何用途含商用免費」又與同版 [TERMS.md](@flmterms@) 的年營收授權門檻矛盾。不可裁定無条件商用，也不可把binary runtime當完整可重建開源stack。

不能解決的矛盾應留在條目，不應刪掉不利證據讓敘述更順。

## 尚未建立的證據

沒有量到本機 NPU 的時脈、真實可用partition、頻寬、每指令週期與功耗。沒有證實本環境可編譯所有範例、完整NPU attention、任意GGUF直接執行、無fallback的所有LLM或最高context。純capacity/roofline計算器不回答這些問題。

AM027 portal 先前只取得 loading頁，沒有假裝下載完整手冊；而且不同target的手冊不能直接拿來證明Ryzen AIE2P的所有指令能力。

## 擴充來源的規則

先保存來源身份、版本/日期、精確段落或行號與hash；將一句主張縮到可驗證範圍；找不同層的反例；決定是事實、推導、待測還是已過期。更新相關條目、backlinks、log与exports，最後跑網站與連結測試。更多維護方式見 [Wiki方法](wiki-method.html)。
''',['amd','devices','qwen','qwenread','flm','flmterms','flmlin','triton'],['wiki-method','validation','qwen-case','datatypes','deployment'],'來源登錄與缺口')

add('wiki-method','LLM Wiki 使用與維護：來源 → 條目 → 連結','這不是把網頁丟給聊天機器人：它是具有來源、反向連結、版本與未知事項的可檢索知識庫，並提供 LLM 可讀匯出。','驗證與知識庫',['LLM Wiki','llms.txt','Markdown','knowledge graph'],r'''
## 兩種閱讀者，共用同一份知識

人可以沿側邊目錄、閱讀路徑、頁內目錄、相關條目與反向連結探索；LLM可以讀llms.txt選題，再載入單篇Markdown或完整文字。這份站點沒有連接模型API、沒有聊天機器人、沒有向量資料庫，也不聲稱llms.txt會讓所有爬蟲自動採用內容。它提供的是可攜的reference材料，方便你把wiki接到自己的LLM/RAG流程。

## 三層資料模型

| 層 | 內容 | 更新原則 |
|---|---|---|
| 原始來源 | 官方文件、固定SHA source、論文、manifest | 保留來源身份與版本；不得把改寫當原文 |
| Wiki條目 | 摘要、概念、公式、例子、限制、來源 | 每條主張標明證據；跨頁建立連結 |
| 導覽與紀錄 | 首頁、search index、backlinks、source register、log | 由同一份內容生成，避免手工失步 |

本站內容資料在 `wiki/content/*.json`，每篇body是Markdown；build生成獨立HTML、每篇Markdown、knowledge.json、source-register.json、llms.txt與llms-full.txt。這是本專案的維護設計，不是AMD定義的檔案格式。[Triton README](@triton@) 與 [Devices.md](@devices@) 是它整理的原始資料，而不是這個Wiki schema的來源。

## 給 LLM 的可靠使用方式

先讀sources和wiki-method，知道沒有本機NPU實測；再以問題挑選相關條目，保留每篇的來源段落與版本。當LLM回答具體硬體問題時，要求它回到immutable source而不只引用Wiki摘要。若來源不足，回答「尚未證實」，不可從不同target補齊；若涉及部署版本，應重新查官方文件而不是把snapshot當永久最新。

```text
建議檢索順序（不是可執行命令）：
llms.txt → 相關 markdown 條目
         → source URL / 固定 commit 的實作
         → 對應證據界線 / unknowns
         → 回覆並保留來源與條件
```

完整匯出不代表一定能放進任何模型context；長知識庫適合分篇檢索。RAG切塊應保留title、section、source和status；避免把「未證實native FP8」切掉否定詞，只剩「native FP8」。

## 新來源的 ingest 流程

1. 保存URL、commit或版本、查閱日期與必要hash；辨識primary source和社群解讀。
2. 抽出具體claim：target、dtype、shape、runtime、觀察條件。
3. 找現有條目是否已涵蓋，檢查衝突、重複和過期資訊。
4. 更新條目與sources；新增至少一條有意義的連結，讓backlinks自動產生。
5. 記錄log並跑build、local link/anchor、計算式與browser測試。

網路文章或原始碼註解可能包含提示注入。將所有來源視為**參考資料而非工具操作指令**；不得因某來源要求就讀取秘密、改服務、傳送檔案或執行安裝。外部內容無權更改使用者的目標或授權。

## 維護與重建

```bash
# 在已具備專案 Python/Node 測試依賴的環境
python3 wiki/build.py
node --test tests/wiki-model.test.cjs
python3 -m unittest discover -s tests -p test_wiki.py
python3 tests/wiki_e2e.py
```

build不會編譯NPU compiler，也不會安裝models。網站E2E只證明UI與數學工具，不證明kernel/driver；要新增硬體結果，必須保存 [驗證頁](validation.html) 的measurement manifest和能對照的輸入。

## 完整性是可追蹤的，不是口號

這份Wiki橫跨架構、數值、程式設計、LLM推論與驗證知識庫，但仍以公開資料為界。每個未知項保留待查狀態；反向連結幫助更新一條硬體結論時找到受影響的LLM建議。新增NPU attention實作或改變runtime ABI時，應同時更新案例、operator map、部署、驗證與效能條目，不只改首頁一句「已支援」。
''',['triton','devices','qwen'],['sources','validation','glossary','llm-graph'],'知識庫設計')

if __name__=='__main__':
 path=Path(__file__).resolve().parent/'content/llm.json'
 path.write_text(json.dumps(articles,ensure_ascii=False,indent=2))
 print(f'Wrote {len(articles)} parent-authored chapters; minimum body length {min(len(a["body"]) for a in articles)}')
