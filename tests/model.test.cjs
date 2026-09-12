const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const file = require('node:path').join(__dirname, '../site/model.js');
test('model module exists', () => assert.ok(fs.existsSync(file), 'working-set calculator not implemented'));
if (fs.existsSync(file)) {
 const { modes, estimate } = require(file);
 test('microtile geometries are distinct', () => {
  assert.deepEqual(modes.i8.shape,[8,8,8]);
  assert.deepEqual(modes.i16.shape,[4,4,8]);
  assert.deepEqual(modes.bf16.shape,[4,8,8]);
  assert.deepEqual(modes.bfp.shape,[8,8,8]);
 });
 test('bf16 double input buffering + fp32 C + 1KiB stack', () => {
  const r=estimate('bf16',64,64,64); assert.equal(r.bytes,50176); assert.equal(r.fits,true); assert.equal(r.geometry,true);
 });
 test('oversized working set is rejected', () => assert.equal(estimate('bf16',128,128,128).fits,false));
 test('geometry validity not conflated with L1 fit', () => { const r=estimate('i8',65,64,64); assert.equal(r.geometry,false); assert.equal(r.fits,true); });
 test('BFP path estimates BF16 source buffers, not compressed storage', () => assert.equal(estimate('bfp',64,64,64).bytes,50176));
 test('unsafe, fractional and nonpositive inputs rejected', () => {
  for(const n of [0,-1,NaN,Infinity,1.5,'64',Number.MAX_SAFE_INTEGER]) assert.throws(()=>estimate('bf16',n,64,64),RangeError);
  assert.throws(()=>estimate('unknown',64,64,64),RangeError);
 });
 test('operations counted as 2 per MAC, not measured throughput', () => assert.equal(estimate('i8',64,64,64).ops,524288));
}
