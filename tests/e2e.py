"""Maintained browser acceptance suite. Run: python3 tests/e2e.py
Requires a loopback preview at XDNA_SITE_URL (defaults to port 18367).
No NPU or external source-link visits. Inline citation links are exempt from 44px target size.
"""
import os,json,math
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('XDNA_EVIDENCE_DIR',str(ROOT/'evidence'))); OUT.mkdir(parents=True,exist_ok=True)
url=os.environ.get('XDNA_SITE_URL','http://127.0.0.1:18367/index.html')
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for name,width,height in [('mobile',390,844),('desktop',1440,1000)]:
        path=OUT/name;path.mkdir(exist_ok=True)
        context=browser.new_context(viewport={'width':width,'height':height},is_mobile=name=='mobile',has_touch=name=='mobile',device_scale_factor=1)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.goto(url,wait_until='networkidle');expect(page).to_have_title('XDNA 2 — From Architecture to Programming')
        expect(page.locator('#tile-array .tile')).to_have_count(48)
        expect(page.locator('#estimate')).to_contain_text('49.0 / 64 KiB')
        page.screenshot(path=str(path/'00-hero.png'))
        for i,id in enumerate(['decision','architecture','types','mma','compiler','programming','performance','sources'],1):
            page.locator(f'nav a[href="#{id}"]').click()
            expect(page).to_have_url(url+'#'+id)
            assert page.locator('#'+id).evaluate('(el)=>el.getBoundingClientRect().top >= 50'),id
            page.screenshot(path=str(path/f'{i:02}-{id}.png'))
        page.locator('nav a[href="#architecture"]').click()
        for i,key in enumerate(['memory','shim','compute']):
            control=page.locator(f'[data-tile="{key}"]');control.scroll_into_view_if_needed()
            assert control.evaluate('(el)=>{let r=el.getBoundingClientRect();let h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return h===el||el.contains(h)}')
            control.click();expect(control).to_have_attribute('aria-pressed','true')
            expect(page.locator('#tile-detail h3')).to_contain_text({'memory':'Memory','shim':'Shim','compute':'Compute'}[key])
            page.locator('#tile-detail').scroll_into_view_if_needed()
            page.screenshot(path=str(path/f'10-{i}-tile-{key}.png'))
        page.locator('nav a[href="#mma"]').click()
        for i,(mode,shape) in enumerate([('i8','[8 × 8]'),('i16','[4 × 4]'),('bfp','[8 × 8]'),('bf16','[4 × 8]')]):
            page.locator('#dtype').select_option(mode);expect(page.locator('#mma-detail')).to_contain_text(shape)
            page.locator('#mma-detail').scroll_into_view_if_needed()
            page.screenshot(path=str(path/f'11-{i}-dtype-{mode}.png'))
        page.locator('#dim-m').fill('128');page.locator('#dim-k').fill('128');page.locator('#dim-n').fill('128')
        expect(page.locator('#estimate')).to_contain_text('容量超限')
        page.locator('#estimate').scroll_into_view_if_needed()
        page.screenshot(path=str(path/'12-capacity-warning.png'))
        page.locator('#dim-m').fill('65');page.locator('#dim-k').fill('64');page.locator('#dim-n').fill('64')
        expect(page.locator('#estimate')).to_contain_text('Microtile 整除：不通過')
        page.locator('#dim-m').fill('0');expect(page.locator('#estimate')).to_contain_text('1–4096')
        page.locator('#estimate').scroll_into_view_if_needed()
        page.screenshot(path=str(path/'13-input-validation.png'))
        page.locator('#dim-m').fill('64');expect(page.locator('#estimate')).to_contain_text('49.0 / 64 KiB')
        page.locator('#estimate').scroll_into_view_if_needed()
        page.screenshot(path=str(path/'14-capacity-normal.png'))
        for download in ['research-manifest.json','guide-notes.md','type-mma-audit.md']:
            link=page.locator(f'.download-grid a[href="{download}"]')
            with page.expect_download() as dl: link.click()
            dl.value.save_as(str(path/download))
            assert (path/download).stat().st_size>100
        # All citation anchors route to real in-page sources (no external navigation).
        for href in page.locator('.cite').evaluate_all('(els)=>[...new Set(els.map(e=>e.getAttribute("href")))]'):
            assert page.locator(href).count()==1
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'document horizontal overflow'
        controls=page.locator('button,input,select').evaluate_all('(els)=>els.map(e=>{let r=e.getBoundingClientRect();return {name:e.id||e.textContent,width:r.width,height:r.height}})')
        assert all(c['height']>=44 and c['width']>=44 for c in controls),controls
        # Capture the full rendered article as sequential viewport slices for direct visual inspection.
        total=page.evaluate('document.documentElement.scrollHeight')
        for i in range(math.ceil(total/(height-70))):
            page.evaluate('(y)=>scrollTo(0,y)',i*(height-70))
            page.screenshot(path=str(path/f'sweep-{i:02}.png'))
        assert not errors,errors
        results.append({'viewport':name,'size':[width,height],'page_console_errors':errors,'document_overflow':False,'controls':controls,'full_article_slices':math.ceil(total/(height-70)),'checks':'anchors, 3 tile states, 4 dtype states, capacity/alignment/invalid input/restoration, 3 downloads, 48 tiles'})
        context.close()
    browser.close()
(OUT/'e2e-metrics.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
print('PASS mobile + desktop:',json.dumps(results,ensure_ascii=False))
