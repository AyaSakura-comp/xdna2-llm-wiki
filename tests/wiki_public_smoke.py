"""Opt-in publication smoke, not a full deployed E2E suite.
Set XDNA_PUBLIC_WIKI_URL to the published index.html URL. No service restarts.
"""
import json,os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
url=os.environ.get('XDNA_PUBLIC_WIKI_URL','')
if not url.startswith('https://raw.githack.com/') or urlsplit(url).path.split('/')[-1]!='index.html':
 raise SystemExit('Explicit XDNA_PUBLIC_WIKI_URL=https://raw.githack.com/.../index.html is required')
base=url.rsplit('/',1)[0]+'/'
out=ROOT/'evidence/spec';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
 try:
  context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'index.html#search',wait_until='networkidle',timeout=45000)
  gate=page.get_by_text('Open the page',exact=True)
  if gate.is_visible():gate.click();page.wait_for_load_state('networkidle')
  expect(page.locator('.wiki-card:visible')).to_have_count(45)
  page.locator('#wiki-search').fill('VLIW pipeline');expect(page.locator('#search-status')).to_contain_text('6 / 45')
  page.locator('#search-status').scroll_into_view_if_needed();page.screenshot(path=str(out/'public-immutable.png'))
  page.locator('.wiki-card[data-slug="spec-index"] a').click();expect(page.locator('h1')).to_contain_text('規格總索引')
  page.locator('.article-body a[href="instruction-cycles.html"]').first.click();expect(page.locator('h1')).to_contain_text('指令週期')
  page.screenshot(path=str(out/'public-cycle.png'));assert not errors,errors
  (out/'public-smoke.json').write_text(json.dumps({'base':base,'checks':['githack consent when shown','45 visible articles','6/45 source-spec search','spec hub link','cycle article navigation'],'page_errors':errors,'scope':'opted-in public smoke; not full deployed E2E'},indent=2))
  print('PASS immutable public smoke');context.close()
 finally:browser.close()
