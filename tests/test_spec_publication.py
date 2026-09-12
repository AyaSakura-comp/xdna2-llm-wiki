"""Source spec enrichment contract. Build before publication tests."""
import unittest,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'wiki-site'
class SpecPublication(unittest.TestCase):
 def test_spec_entrypoints_and_exports(self):
  self.assertTrue((OUT/'spec-index.html').exists(),'Specification coverage hub must be generated')
  slugs=['spec-index','isa-registers','isa-encoding','isa-instructions','instruction-cycles','vliw-pipeline','software-pipelining','tile-microarchitecture','interconnect','dma-registers','events-debug','spec-gaps']
  records={r['slug']:r for r in json.loads((OUT/'knowledge.json').read_text())}
  full=(OUT/'llms-full.txt').read_text()
  for s in slugs:
   self.assertIn(s,records);self.assertIn(records[s]['title'],full);self.assertTrue((OUT/'markdown'/f'{s}.md').exists())
  for f in ['isa-source-index.json','scheduling-model.json','registers-events.json']:
   self.assertEqual((ROOT/'wiki/spec-data'/f).read_bytes(),(OUT/'spec-data'/f).read_bytes())
   self.assertIn('spec-data/'+f,(OUT/'llms.txt').read_text())
  self.assertIn('spec-index.html',(OUT/'index.html').read_text())
  self.assertIn('../spec-data/registers-events.json',(OUT/'markdown/dma-registers.md').read_text())
 def test_search_data_has_content_version(self):
  from bs4 import BeautifulSoup
  from urllib.parse import urlsplit,parse_qs
  soup=BeautifulSoup((OUT/'spec-index.html').read_text(),'html.parser')
  script=next(s['src'] for s in soup.select('script[src]') if 'search-data.js' in s['src'])
  self.assertRegex(parse_qs(urlsplit(script).query).get('v',[''])[0],r'^[a-f0-9]{12}$','Updated articles must not use cached old search data')
 def test_source_dataset_manifest(self):
  path=OUT/'spec-manifest.json';self.assertTrue(path.exists(),'LLM dataset manifest must exist')
  import hashlib
  rows=json.loads(path.read_text())['datasets'];self.assertEqual(len(rows),3)
  for r in rows:
   raw=(OUT/r['path']).read_bytes();self.assertEqual(r['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(r['bytes'],len(raw))
  self.assertIn('spec-manifest.json',(OUT/'llms.txt').read_text())
 def test_source_license_notices_are_retained(self):
  p=OUT/'spec-NOTICES.txt';self.assertTrue(p.exists(),'Raw source excerpts must retain upstream notices')
  text=p.read_text();self.assertIn('Apache License',text);self.assertIn('Permission is hereby granted',text)
  self.assertIn('spec-NOTICES.txt',(OUT/'llms.txt').read_text())
