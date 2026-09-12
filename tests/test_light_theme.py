"""Rendered theme contract: python3 -m unittest discover -s tests -p test_light_theme.py"""
import re
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = (Path(__file__).resolve().parents[1] / 'site/index.html').as_uri()

def luminance(rgb):
    parts = [int(x) / 255 for x in re.findall(r'\d+', rgb)[:3]]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in parts]
    return sum(v * w for v, w in zip(linear, [.2126, .7152, .0722]))

def contrast(a, b):
    x, y = sorted([luminance(a), luminance(b)])
    return (y + .05) / (x + .05)

class LightTheme(unittest.TestCase):
    def test_white_theme_and_readable_interactive_surfaces(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
            for width, height in [(390, 844), (1440, 1000)]:
                page = browser.new_page(viewport={'width': width, 'height': height}, color_scheme='dark')
                page.goto(SITE)
                self.assertEqual(page.locator('html').evaluate('(e)=>getComputedStyle(e).colorScheme'), 'light')
                self.assertEqual(page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor'), 'rgb(255, 255, 255)')
                for text, background in [('body','body'), ('.lead','body'), ('code','pre'), ('th','th'), ('.tile','.tile'), ('.tile.mem','.tile.mem'), ('.tile.shim','.tile.shim'), ('.native','.result'), ('.emul','.note'), ('#dtype','#dtype'), ('button[aria-pressed="true"]','button[aria-pressed="true"]')]:
                    fg = page.locator(text).first.evaluate('(e)=>getComputedStyle(e).color')
                    bg = page.locator(background).first.evaluate('(e)=>getComputedStyle(e).backgroundColor')
                    self.assertGreaterEqual(contrast(fg,bg), 4.5, (width,text,fg,bg))
                link = page.locator('.button-link').first
                link.hover()
                fg = link.evaluate('(e)=>getComputedStyle(e).color')
                bg = link.evaluate('(e)=>getComputedStyle(e).backgroundColor')
                self.assertGreaterEqual(contrast(fg,bg),4.5,'hover link text')
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.close()
            browser.close()
