import unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self): super().__init__(); self.ids=[]; self.links=[]; self.main_count=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='main': self.main_count+=1
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a': self.links.append(a.get('href',''))
class Site(unittest.TestCase):
    def test_site_exists(self): self.assertTrue((ROOT/'site/index.html').is_file(), 'guide not implemented')
    def test_content_and_links(self):
        f=ROOT/'site/index.html'
        if not f.exists(): self.skipTest('guide missing')
        text=f.read_text(); p=Page(); p.feed(text)
        for id in ['overview','architecture','types','mma','compiler','programming','performance','sources']:
            self.assertIn(id,p.ids)
        self.assertEqual(len(p.ids),len(set(p.ids)))
        self.assertEqual(p.main_count,1,'exactly one main landmark')
        for link in p.links:
            if link.startswith('#'): self.assertIn(link[1:],p.ids)
            elif link and not link.startswith(('http:','https:','mailto:')):
                self.assertTrue((ROOT/'site'/link.split('#')[0]).is_file(),link)
        for term in ['AIE2P','aie2p-none-unknown-elf','尚未','Triton-XDNA','Peano','BFP16','64 KiB','FP32']:
            self.assertIn(term,text)
        self.assertNotIn('http://',text)
if __name__=='__main__': unittest.main()
