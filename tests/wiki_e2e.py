"""Self-hosted wiki acceptance. python3 tests/wiki_e2e.py (no NPU, no external links)."""
import json, threading, os
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'wiki-site';OUT=Path(os.environ.get('XDNA_WIKI_EVIDENCE_DIR',ROOT/'evidence/wiki'))
OUT.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(SITE)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
url=f'http://127.0.0.1:{server.server_port}'
(OUT/'fixture.json').write_text(json.dumps({'pid':os.getpid(),'loopback_url':url,'site':str(SITE),'lifecycle':'threaded server shutdown in finally; not a background service'}))
records=json.loads((SITE/'knowledge.json').read_text());metrics=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  for name,w,h in [('mobile',390,844),('desktop',1440,1000)]:
   path=OUT/name;path.mkdir(exist_ok=True)
   context=browser.new_context(viewport={'width':w,'height':h},is_mobile=name=='mobile',has_touch=name=='mobile',color_scheme='dark',permissions=['clipboard-read','clipboard-write'])
   page=context.new_page();errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   page.goto(url+'/index.html',wait_until='networkidle')
   expect(page.locator('h1')).to_contain_text('讀懂 XDNA 2')
   assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
   assert page.locator('html').evaluate('(e)=>getComputedStyle(e).colorScheme')=='light'
   page.screenshot(path=str(path/'00-home.png'));page.screenshot(path=str(path/'00-home-full.png'),full_page=True)
   # Search, category, no-results/injection-looking input, reset and URL state.
   page.locator('#wiki-search').fill('Qwen CPU')
   expect(page.locator('#search-status')).not_to_contain_text('顯示 0 /')
   assert all('qwen' in (r['title']+r['summary']+r['body']+' '.join(r['tags'])).lower() for r in records if page.locator(f'[data-slug="{r["slug"]}"]').is_visible())
   page.locator('#search-status').scroll_into_view_if_needed();page.screenshot(path=str(path/'01-search.png'))
   page.locator('#wiki-search').fill('');page.locator('#category').select_option('架構')
   expect(page.locator('.wiki-card:visible')).to_have_count(sum(r['category']=='架構' for r in records))
   page.screenshot(path=str(path/'02-category.png'))
   page.locator('#wiki-search').fill('<img src=x onerror=alert(1)>')
   expect(page.locator('#no-results')).to_be_visible();assert page.locator('#search-results img').count()==0
   page.screenshot(path=str(path/'03-empty-search.png'))
   page.locator('#reset-search').click();expect(page.locator('.wiki-card:visible')).to_have_count(len(records))
   # Every primary destination via a real sidebar pointer click.
   for i,r in enumerate(records,1):
    menu=page.locator('#nav-menu')
    if not menu.evaluate('(e)=>e.open'):page.locator('#nav-menu summary').click()
    link=page.locator(f'.navtree a[href="{r["slug"]}.html"]');link.click()
    expect(page.locator('h1')).to_have_text(r['title'])
    expect(page.locator('.navtree [aria-current="page"]')).to_have_count(1)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),r['slug']
    controls=page.locator('.wordmark,.header-links a,button,input,select,summary').evaluate_all('''els=>els.filter(e=>e.getBoundingClientRect().height>0).map(e=>({name:e.id||e.textContent.slice(0,25),w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}))''')
    assert all(c['w']>=44 and c['h']>=44 for c in controls),(name,r['slug'],controls)
    page.screenshot(path=str(path/f'{i:02}-{r["slug"]}-top.png'))
    headings=page.locator('.article-body h2');headings.nth(headings.count()//2).scroll_into_view_if_needed()
    page.screenshot(path=str(path/f'{i:02}-{r["slug"]}-middle.png'))
    page.locator('.link-panels').scroll_into_view_if_needed();page.screenshot(path=str(path/f'{i:02}-{r["slug"]}-bottom.png'))
    page.screenshot(path=str(path/f'{i:02}-{r["slug"]}-full.png'),full_page=True)
    # TOC anchors land below sticky bar, not under it.
    toc=page.locator('.toc a').first;target=toc.get_attribute('href');toc.click()
    expect(page).to_have_url(url+'/'+r['slug']+'.html'+target)
    assert page.locator(target).evaluate('(e)=>e.getBoundingClientRect().top')>=72
   # Related links and backlinks are real navigation, not rendered decorations.
   page.goto(url+'/attention.html');page.locator('.related-links a[href="kv-cache.html"]').first.click()
   expect(page.locator('h1')).to_contain_text('KV cache')
   expect(page.locator('#kv-result')).to_contain_text('1.0000 GiB')
   page.locator('#kv-batch').fill('2');expect(page.locator('#kv-result')).to_contain_text('2.0000 GiB')
   page.locator('#kv-result').scroll_into_view_if_needed();page.screenshot(path=str(path/'80-kv-scaled.png'))
   page.locator('#kv-tokens').fill('0');expect(page.locator('#kv-result')).to_have_class('result error')
   page.screenshot(path=str(path/'81-kv-invalid.png'))
   page.locator('#kv-tokens').fill('8192');page.locator('#kv-batch').fill('1');page.locator('#kv-bytes').select_option('1')
   expect(page.locator('#kv-result')).to_contain_text('0.5000 GiB');page.screenshot(path=str(path/'82-kv-recovered.png'))
   page.goto(url+'/performance.html');expect(page.locator('#gemm-result')).to_contain_text('不是 NPU 實測')
   page.locator('#gemm-m').fill('1');page.locator('#gemm-result').scroll_into_view_if_needed();page.screenshot(path=str(path/'83-gemv.png'))
   page.locator('#gemm-tops').fill('0');expect(page.locator('#gemm-result')).to_have_class('result error');page.screenshot(path=str(path/'84-gemm-invalid.png'))
   page.locator('#gemm-tops').fill('0.01');expect(page.locator('#gemm-result')).to_contain_text('至少為 0.1')
   page.locator('#gemm-tops').fill('0.1');expect(page.locator('#gemm-result')).not_to_have_class('result error')
   page.locator('#gemm-bandwidth').fill('0.01');expect(page.locator('#gemm-result')).to_contain_text('至少為 0.1')
   page.locator('#gemm-bandwidth').fill('50');page.locator('#gemm-tops').fill('10');page.locator('#gemm-m').fill('512');expect(page.locator('#gemm-result')).not_to_have_class('result error');page.screenshot(path=str(path/'85-gemm-recovered.png'))
   # Clipboard: actual browser permission and clipboard contents, no API mock.
   page.goto(url+'/gemm.html');copy=page.locator('.copy-code').first;expected=copy.evaluate('(e)=>e.nextElementSibling.textContent');copy.click();expect(copy).to_have_text('已複製')
   assert page.evaluate('navigator.clipboard.readText()')==expected
   page.screenshot(path=str(path/'86-copy.png'))
   # A download on an article plus all machine-readable home exports.
   with page.expect_download() as d:page.locator('.article-meta a[download]').click()
   d.value.save_as(str(path/'gemm.md'))
   page.goto(url+'/index.html')
   for file in ['llms-full.txt','knowledge.json','source-register.json']:
    with page.expect_download() as d:page.locator(f'.downloads a[href="{file}"]').click()
    d.value.save_as(str(path/file));assert (path/file).stat().st_size>100
   # Specification hub, topic search and actual portable JSON dataset downloads.
   page.locator('.path-grid a[href="spec-index.html"]').click();expect(page.locator('h1')).to_contain_text('規格總索引')
   page.locator('.article-body a[href="instruction-cycles.html"]').first.click();expect(page.locator('h1')).to_contain_text('指令週期')
   page.goto(url+'/index.html');page.locator('#wiki-search').fill('VLIW pipeline');expect(page.locator('#search-status')).not_to_contain_text('顯示 0 /')
   page.locator('#search-status').scroll_into_view_if_needed();page.screenshot(path=str(path/'90-spec-search.png'))
   response=page.request.get(url+'/spec-manifest.json');assert response.ok;manifest=response.json()
   import hashlib
   for dataset in manifest['datasets']:
    response=page.request.get(url+'/'+dataset['path']);assert response.ok;raw=response.body()
    assert hashlib.sha256(raw).hexdigest()==dataset['sha256'];assert json.loads(raw)['source_commit']==dataset['source_commit']
   page.goto(url+'/interconnect.html');table=page.locator('.table-scroll').first
   if name=='mobile':
    table.scroll_into_view_if_needed();assert table.evaluate('(e)=>e.scrollWidth>e.clientWidth')
    table.focus();page.keyboard.press('ArrowRight');page.wait_for_function('(e)=>e.scrollLeft>0',arg=table.element_handle())
    page.screenshot(path=str(path/'91-table-keyboard-scroll.png'))
   # Menu toggle, skip link focus and no-JS fallback basics.
   page.goto(url+'/index.html');page.keyboard.press('Tab');expect(page.locator('.skip')).to_be_focused()
   page.keyboard.press('Enter');expect(page.locator('#main')).to_be_focused()
   assert not errors,errors
   metrics.append({'viewport':name,'size':[w,h],'articles':len(records),'console_errors':errors,'horizontal_overflow':False,'checks':['full-text search','category','empty+reset','all sidebar links','all TOCs','related link','KV valid/error/recovery','GEMM valid/error/recovery','clipboard','4 downloads','spec navigation+search','3 dataset HTTP bytes+hashes','table internal keyboard scroll (mobile)','light OS-dark override'],'visual_evidence':'top/middle/bottom and full-page captures; no continuous video playback audit'})
   context.close()
  context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
  page=context.new_page();page.goto(url+'/index.html');expect(page.locator('.wiki-card')).to_have_count(len(records));page.locator('#nav-menu summary').click();page.locator('.navtree a[href="system.html"]').click();expect(page.locator('h1')).to_contain_text('XDNA')
  page.screenshot(path=str(OUT/'no-js.png'));context.close();browser.close()
 (OUT/'e2e-metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False));print('PASS',json.dumps(metrics,ensure_ascii=False))
finally:
 server.shutdown();server.server_close();thread.join(timeout=2)
