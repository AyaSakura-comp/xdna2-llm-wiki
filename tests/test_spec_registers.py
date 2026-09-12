import unittest, importlib.util, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RegisterExtraction(unittest.TestCase):
 def module(self):
  p=ROOT/'wiki/extract_registers.py'
  self.assertTrue(p.exists(),'Read-only AIE2P register extractor must exist')
  spec=importlib.util.spec_from_file_location('register_extract',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_exact_literals_and_uninterpreted_expressions(self):
  m=self.module();text='#define XAIE2PGBL_A 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\n#define XAIE2PGBL_B 17U\n#define XAIE2PGBL_C (1 << 5)\n#define OTHER 3\n#define XAIE2PGBL_FUNC(x) (x)\n'
  rows=m.parse_defines(text,'https://example.com/source')
  self.assertEqual([r['name'] for r in rows],['XAIE2PGBL_A','XAIE2PGBL_B','XAIE2PGBL_C'])
  self.assertEqual(rows[0]['integer_decimal'],str(2**128-1));self.assertEqual(rows[1]['integer_decimal'],'17');self.assertIsNone(rows[2]['integer_decimal'])
  self.assertEqual(rows[0]['source_url'],'https://example.com/source#L1-L1')
 def test_multiline_records_preserve_range(self):
  rows=self.module().parse_defines('#define XAIE2PGBL_A \\\n  (1 + 2)\n#define XAIE2P_EVENTS_CORE_MEMORY_STALL 23U\n','https://example.com/source')
  self.assertEqual(len(rows),2);self.assertEqual(rows[0]['line_end'],2);self.assertEqual(rows[1]['integer_decimal'],'23')
 def test_catalog_uses_pinned_objects_not_mutable_worktree(self):
  from unittest.mock import patch
  m=self.module()
  with patch.object(Path,'read_bytes',side_effect=AssertionError('Mutable worktree must not be the source')):
   data=m.extract()
  self.assertGreater(len(data['records']),15000)
 def test_full_pinned_headers_and_provenance(self):
  m=self.module();data=m.extract()
  self.assertEqual(data['source_commit'],'8849e208bdcc533b20a0ed3f95c1ce961dee9c3a')
  self.assertGreater(len(data['records']),15000)
  for s in data['sources']:
   text=(ROOT/'sources/mlir-aie/third_party/aie-rt'/s['path']).read_text()
   expected=sum(bool(re.match(r'#define\s+(?:XAIE2PGBL_|XAIE2P_EVENTS_)\w+\s+\S',line)) for line in text.splitlines())
   self.assertEqual(s['record_count'],expected)
   lines=text.splitlines()
   for r in [r for r in data['records'] if r['source_path']==s['path']]:
    self.assertIn(r['name'],lines[r['line_start']-1]);self.assertIn('/'+data['source_commit']+'/',r['source_url'])
  lookup={r['name']:r for r in data['records']}
  self.assertEqual(lookup['XAIE2P_EVENTS_CORE_MEMORY_STALL']['integer_decimal'],'23')
  self.assertEqual(lookup['XAIE2PGBL_CORE_MODULE_PROGRAM_MEMORY']['integer_decimal'],str(0x20000))
