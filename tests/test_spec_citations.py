"""Validate fixed-source citation line ranges without external network access."""
import json,re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SpecCitations(unittest.TestCase):
 def test_all_pinned_source_ranges_exist(self):
  roots={'llvm-aie':ROOT/'sources/llvm-aie','mlir-aie':ROOT/'sources/mlir-aie','aie-rt':ROOT/'sources/mlir-aie/third_party/aie-rt'};cache={};checked=0
  for p in (ROOT/'wiki/content').glob('spec*.json'):
   for a in json.loads(p.read_text()):
    for s in a['sources']:
     m=re.fullmatch(r'https://github.com/Xilinx/(llvm-aie|mlir-aie|aie-rt)/blob/([a-f0-9]{40})/(.*?)#L(\d+)-L(\d+)',s['url'])
     if not m:continue
     repo,sha,path,lo,hi=m.groups();key=(repo,sha,path)
     if key not in cache:cache[key]=subprocess.check_output(['git','-C',str(roots[repo]),'show',f'{sha}:{path}']).splitlines()
     self.assertTrue(1<=int(lo)<=int(hi)<=len(cache[key]),(a['slug'],s['url'],len(cache[key])))
     checked+=1
  self.assertGreater(checked,100)
