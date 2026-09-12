"""ISA catalog contract; stdlib only. Run: python3 -m unittest discover -s tests -p test_spec_isa.py -v."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/llvm-aie'
COMMIT = '386ca5c6634a84bb224b7248e79df8edabf0722f'
TARGET = 'llvm/lib/Target/AIE/aie2p'
EXCLUDED = {'AIE2PGenSchedule.td', 'AIE2PSchedule.td', 'ExtraItinDecls.td', 'ExtraItineraries.td'}


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('extract_isa', ROOT / 'wiki/extract_isa.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_lexer_balances_and_ignores_comments_strings(self):
        text = '// def FAKE;\nclass Box<int n> { string s = "def BAD; {"; /* } */ }\nlet X = 1 in { def Real : Box<2>; }\nmulticlass M { def NAME # _x : Box<1>; }\ndefm Prefix : M;\ndef : Box<3>;\n'
        records = self.module.extract_declarations(text)
        self.assertEqual([(r['kind'], r['name']) for r in records],
                         [('class', 'Box'), ('def', 'Real'), ('multiclass', 'M'),
                          ('def', 'NAME # _x'), ('defm', 'Prefix'), ('def', None)])
        self.assertEqual(records[0]['line_start'], 2)
        self.assertTrue(records[0]['raw_text'].endswith('}'))
        self.assertIn('/* } */', records[0]['raw_text'])
        self.assertEqual(records[-1]['raw_text'], 'def : Box<3>;')

    def test_defset_name_and_opaque_code_block(self):
        records = self.module.extract_declarations('defset list<Foo> Group = { def : Foo; }\nclass C { code x = [{ def NOT_REAL; }]; }')
        self.assertEqual([(r['kind'], r['name']) for r in records],
                         [('defset', 'Group'), ('def', None), ('class', 'C')])

    def test_unclosed_definition_rejected(self):
        with self.assertRaises(ValueError):
            self.module.extract_declarations('def Broken : Foo { bits<8> x;')

    def test_catalog_roundtrip_and_complete_file_scope(self):
        actual = self.module.build_catalog(SOURCE)
        committed = json.loads((ROOT / 'wiki/spec-data/isa-source-index.json').read_text())
        self.assertEqual(actual, committed)
        self.assertEqual(actual['source_commit'], COMMIT)
        self.assertIn('not fully instantiated', actual['scope'])
        self.assertIn('silicon', actual['scope'])
        expected = {p.relative_to(SOURCE).as_posix() for p in (SOURCE / TARGET).glob('*.td') if p.name not in EXCLUDED}
        self.assertEqual({f['source_path'] for f in actual['files']}, expected)
        self.assertEqual(actual['counts'], {'files': 16, 'records': 2401,
                         'by_kind': {'class': 167, 'def': 2163, 'defm': 59, 'defset': 6, 'multiclass': 6}})
        self.assertEqual(next(f['record_count'] for f in actual['files'] if f['source_path'].endswith('AIE2PGenInstrInfo.td')), 879)
        self.assertEqual(actual['counts']['records'], len(actual['records']))
        self.assertEqual(actual['counts']['by_kind'], dict(collections.Counter(r['kind'] for r in actual['records'])))
        for f in actual['files']:
            raw = (SOURCE / f['source_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), f['sha256'])
            self.assertEqual(f['record_count'], sum(r['source_path'] == f['source_path'] for r in actual['records']))
        ids = set()
        for r in actual['records']:
            self.assertNotIn(r['id'], ids)
            ids.add(r['id'])
            text = (SOURCE / r['source_path']).read_text()
            self.assertEqual(text[r['offset_start']:r['offset_end']], r['raw_text'])
            self.assertEqual(text.count('\n', 0, r['offset_start']) + 1, r['line_start'])
            self.assertEqual(text.count('\n', 0, r['offset_end'] - 1) + 1, r['line_end'])
            self.assertEqual(r['source_url'], f"https://github.com/Xilinx/llvm-aie/blob/{COMMIT}/{r['source_path']}#L{r['line_start']}-L{r['line_end']}")
            self.assertNotIn('/aie2ps/', r['source_path'])

    def test_cli_reproducible_and_read_only(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE / TARGET).glob('*.td')}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'catalog.json'
            subprocess.run([sys.executable, str(ROOT / 'wiki/extract_isa.py'), '--source-root', str(SOURCE), '--output', str(output)], check=True, capture_output=True)
            self.assertEqual(output.read_bytes(), (ROOT / 'wiki/spec-data/isa-source-index.json').read_bytes())
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})

    def test_wrong_commit_and_modified_input_rejected(self):
        original = self.module.git
        with patch.object(self.module, 'git', return_value=b'wrong-commit\n'):
            with self.assertRaisesRegex(ValueError, 'Expected pinned commit'):
                self.module.build_catalog(SOURCE)
        def altered(root, *args):
            return b'modified source' if args[0] == 'show' else original(root, *args)
        with patch.object(self.module, 'git', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'differs from pinned blob'):
                self.module.build_catalog(SOURCE)

    def test_output_into_source_tree_rejected(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'wiki/extract_isa.py'),
                               '--output', str(SOURCE / 'isa-forbidden.json')], capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(b'outside the read-only source tree', proc.stderr)
        self.assertFalse((SOURCE / 'isa-forbidden.json').exists())

    def test_documented_bit_arithmetic_and_source_form(self):
        text = (SOURCE / TARGET / 'AIE2PGenInstrInfo.td').read_text()
        self.assertIn('let alu = {s0, d0, s1, 0b0000, 0b1};', text)
        alu = (2 << 15) | (1 << 10) | (3 << 5) | 1
        self.assertEqual(alu, 0x10461)
        self.assertEqual((2 << 27) | (alu << 7) | (1 << 4) | 8, 0x10823098)
        self.assertEqual((2 << 1) | (3 << 3) | (1 << 5), 0x3c)
        composite = (SOURCE / TARGET / 'AIE2PCompositeFormats.td').read_text()
        self.assertIn('let inst_alu = {0b00010, alu, 0b001};', composite)
        self.assertIn('let instr128 = {lda, ldb, st, 0b0, alu, mv, 0b1, vec};', composite)
        self.assertEqual(20 + 17 + 20 + 1 + 20 + 22 + 1 + 26 + 1, 128)

    def test_articles_contract(self):
        articles = json.loads((ROOT / 'wiki/content/spec-isa.json').read_text())
        slugs = {'isa-registers', 'isa-encoding', 'isa-instructions'}
        self.assertEqual({a['slug'] for a in articles}, slugs)
        for a in articles:
            self.assertEqual(set(a), {'slug', 'title', 'summary', 'category', 'status', 'tags', 'body', 'related', 'sources'})
            self.assertEqual(a['category'], '架構')
            self.assertGreaterEqual(a['body'].count('## '), 4)
            self.assertGreaterEqual(len(a['body']), 800)
            self.assertIn('|---', a['body'])
            self.assertIn('spec-data/isa-source-index.json', a['body'])
            self.assertIn('arch 21', a['body'])
            self.assertTrue(set(a['related']) <= slugs | {'isa', 'compute', 'datatypes', 'mma'})
            for source in a['sources']:
                self.assertEqual(set(source), {'label', 'url', 'note'})
                self.assertIn('/' + COMMIT + '/', source['url'])
                self.assertIn(source['url'], a['body'])
                path, fragment = source['url'].split('/' + COMMIT + '/')[1].split('#')
                start, end = map(int, fragment.replace('L', '').split('-'))
                self.assertLessEqual(end, len((SOURCE / path).read_text().splitlines()))
                self.assertLessEqual(start, end)


if __name__ == '__main__':
    unittest.main()
