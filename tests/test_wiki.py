"""Static publication contracts. Run after python3 wiki/build.py."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'wiki-site'

class WikiPublication(unittest.TestCase):
 def test_glossary_exposed_pipeline_claim(self):
  data=json.loads((ROOT/'wiki/content/llm.json').read_text())
  text=next(r['body'] for r in data if r['slug']=='glossary')
  self.assertNotIn('有資料依賴仍會 stall',text)
  self.assertIn('外露管線',text)
 def test_reject_active_authored_markup(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('wiki_build',ROOT/'wiki/build.py')
  build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
  for body in ['<base href="https://example.com">','<meta http-equiv="refresh" content="0;url=https://example.com">','<link rel="stylesheet" href="https://example.com/x.css">']:
   with self.assertRaises(ValueError):build.render_body({'body':body})
 def test_publication_and_llm_exports(self):
  self.assertTrue((OUT/'index.html').exists(),'Wiki home must be generated')
  records=json.loads((OUT/'search-index.json').read_text())
  self.assertGreaterEqual(len(records),26)
  self.assertEqual(len({x['slug'] for x in records}),len(records))
  for name in ['llms.txt','llms-full.txt','knowledge.json','source-register.json','log.md']:
   self.assertGreater((OUT/name).stat().st_size,100,name)
  for record in records:
   self.assertTrue((OUT/f"{record['slug']}.html").exists())
   self.assertIn(record['title'],(OUT/'markdown'/f"{record['slug']}.md").read_text())
   self.assertGreater(len(record['body']),800,record['slug'])
 def test_markdown_source_evidence_paths(self):
  text=(OUT/'markdown/sources.md').read_text()
  self.assertIn('(../research-manifest.json)',text)
  self.assertIn('(../type-mma-audit.md)',text)
  self.assertIn('(../guide/index.html)',text)
 def test_all_local_links_anchors_assets_and_semantic_structure(self):
  self.assertTrue((OUT/'index.html').exists(),'Run wiki/build.py first')
  for path in OUT.glob('*.html'):
   soup=BeautifulSoup(path.read_text(),'html.parser')
   self.assertEqual(len(soup.find_all('main')),1,path.name)
   self.assertEqual(len(soup.find_all('h1')),1,path.name)
   ids=[e['id'] for e in soup.select('[id]')]
   self.assertEqual(len(ids),len(set(ids)),path.name)
   for el in soup.select('a[href],script[src],link[href],img[src]'):
    raw=el.get('href',el.get('src',''));u=urlsplit(raw)
    if u.scheme or raw.startswith('//'):continue
    target=(path.parent/unquote(u.path)) if u.path else path
    self.assertTrue(target.exists(),(path.name,raw))
    if u.fragment and target.suffix=='.html':
     doc=soup if target==path else BeautifulSoup(target.read_text(),'html.parser')
     self.assertIsNotNone(doc.find(id=unquote(u.fragment)),(path.name,raw))
 def test_sources_backlinks_and_dangerous_urls(self):
  self.assertTrue((OUT/'knowledge.json').exists(),'Knowledge graph export must exist')
  records=json.loads((OUT/'knowledge.json').read_text()); slugs={r['slug'] for r in records}
  for r in records:
   self.assertTrue(r['sources'],r['slug'])
   self.assertTrue(r['related'],r['slug'])
   for dest in r['related']:
    self.assertIn(dest,slugs)
    other=next(x for x in records if x['slug']==dest)
    self.assertIn(r['slug'],other['backlinks'])
   soup=BeautifulSoup((OUT/f"{r['slug']}.html").read_text(),'html.parser')
   self.assertGreaterEqual(len(soup.select('.article-body h2')),4,r['slug'])
   self.assertFalse(soup.select('.article-body script,.article-body iframe'))
   for a in soup.select('a[href]'):
    self.assertNotIn(urlsplit(a['href']).scheme.lower(),['javascript','data','file'])
