const test=require('node:test');
const assert=require('node:assert/strict');
const m=require('../wiki/assets/model.js');
test('search combines case-insensitive terms and category, includes body',()=>{
 const data=[{title:'Qwen2.5',summary:'NPU routing',body:'CPU fallback',category:'LLM推論',tags:['KV']},{title:'DMA',summary:'movement',body:'NPU',category:'架構',tags:[]}];
 assert.equal(m.search(data,'QWEN cpu','全部')[0].title,'Qwen2.5');
 assert.equal(m.search(data,'NPU','架構').length,1);
 assert.equal(m.search(data,'missing','全部').length,0);
 assert.equal(m.search(data,'  ','全部').length,2);
 assert.equal(m.search(data,'<script>','全部').length,0);
});
test('GQA KV cache payload: batch1 layer32 KVheads8 head128 context8192 BF16 = 1GiB',()=>{
 assert.equal(m.kv({batch:1,layers:32,heads:8,dim:128,tokens:8192,bytes:2}).total,1073741824);
 assert.equal(m.kv({batch:2,layers:32,heads:8,dim:128,tokens:8192,bytes:2}).total,2147483648);
});
test('KV append size and payload scale linearly with KV heads, not query heads',()=>{
 const r=m.kv({batch:1,layers:24,heads:2,dim:64,tokens:4096,bytes:2});
 assert.equal(r.total,50331648);assert.equal(r.perToken,12288);
});
test('invalid KV dimensions and overflowing sizes rejected',()=>{
 for(const x of [0,-1,1.5,NaN,Infinity])assert.throws(()=>m.kv({batch:x,layers:32,heads:8,dim:128,tokens:8192,bytes:2}));
 assert.throws(()=>m.kv({batch:1000000,layers:1000000,heads:1000000,dim:1000000,tokens:1000000,bytes:2}));
});
test('ideal weight payload explicitly excludes scales and workspace',()=>{
 assert.equal(m.weights(7,4),3500000000);assert.equal(m.weights(.5,16),1000000000);
 assert.throws(()=>m.weights(0,4));assert.throws(()=>m.weights(7,3));
});
test('GEMM lower bound: beta0, reads A/B once and writes C once',()=>{
 const r=m.gemm({m:64,k:64,n:64,inputBytes:2,outputBytes:4,tops:10,bandwidth:50});
 assert.equal(r.ops,524288);assert.equal(r.bytes,32768);assert.equal(r.intensity,16);
 assert.equal(r.computeSeconds,524288/1e13);assert.equal(r.memorySeconds,32768/50e9);
 assert.equal(r.lowerSeconds,Math.max(r.computeSeconds,r.memorySeconds));assert.equal(r.bottleneck,'memory');
});
test('GEMM enforces UI 0.1 minimum and never accepts underflow timing inputs',()=>{
 const base={m:512,k:4096,n:4096,inputBytes:2,outputBytes:4,tops:10,bandwidth:50};
 for(const value of [0.01,1e-320])for(const key of ['tops','bandwidth'])assert.throws(()=>m.gemm({...base,[key]:value}));
 assert(Number.isFinite(m.gemm({...base,tops:.1,bandwidth:.1}).lowerSeconds));
});
test('decode GEMV has low intensity relative to large-M prefill, not a measured speed',()=>{
 const base={k:4096,n:4096,inputBytes:2,outputBytes:4,tops:10,bandwidth:50};
 assert(m.gemm({...base,m:512}).intensity>m.gemm({...base,m:1}).intensity);
 assert.throws(()=>m.gemm({...base,m:1,tops:0}));assert.throws(()=>m.gemm({...base,m:1,bandwidth:Infinity}));
});
