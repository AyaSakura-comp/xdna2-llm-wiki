#!/usr/bin/env python3
"""Read-only, stdlib AIE2P TableGen SOURCE DEFINITION inventory (schema v1).

Reproduce: python3 wiki/extract_isa.py --output wiki/spec-data/isa-source-index.json
See notes/spec-isa-audit.md for scope, schema, tests and deliberate omissions.
No TableGen expansion, compilation, network access, or source-tree writes.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

COMMIT = '386ca5c6634a84bb224b7248e79df8edabf0722f'
TARGET = 'llvm/lib/Target/AIE/aie2p'
EXCLUDED = {'AIE2PGenSchedule.td', 'AIE2PSchedule.td', 'ExtraItinDecls.td', 'ExtraItineraries.td'}
BASE_URL = f'https://github.com/Xilinx/llvm-aie/blob/{COMMIT}/'
SCOPE = ('Regex-source records, not fully instantiated TableGen opcodes, aliases, expanded multiclasses, '
         'or a silicon complete ISA. Inventories every class/multiclass/def/defm/defvar/defset token '
         'outside comments and strings in all immediate aie2p/*.td except four scheduling/itinerary files. '
         'Includes nested and anonymous declarations; does not evaluate foreach, let, inheritance, '
         'includes, predicates, aliases, or compiler patterns. Shared AIE base declarations and clang '
         'C/API headers are not recursively cataloged. AIE2P arch 21 only, not AIE2PS arch 22. '
         'Counts are source declarations, never instruction counts or hardware throughput.')
# Replacing lexical trivia with spaces preserves offsets and line numbers. Code blocks
# [{...}] are opaque TableGen strings, not places to discover declaration tokens.
TRIVIA = re.compile(r'//[^\n]*|/\*.*?\*/|\[\{.*?\}\]|"(?:\\.|[^"\\])*"', re.S)
DECLARATION = re.compile(r'\b(class|multiclass|defm|defvar|defset|def)\b')


def mask_trivia(text):
    return TRIVIA.sub(lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text)


def extract_declarations(text):
    """Return lexical declaration slices, retaining nested records independently.

    Offsets are zero-based Unicode character offsets, end-exclusive. Lines are
    one-based inclusive. Name is raw unevaluated header expression, or null for
    anonymous def/defm; raw_text retains original comments, whitespace and body.
    """
    masked = mask_trivia(text)
    records = []
    for match in DECLARATION.finditer(masked):
        start = match.start()
        angle = paren = square = brace = 0
        body = False
        end = None
        for i in range(match.end(), len(masked)):
            c = masked[i]
            if body:
                if c == '{':
                    brace += 1
                elif c == '}':
                    brace -= 1
                    if brace == 0:
                        end = i + 1
                        break
            else:
                if c == '<':
                    angle += 1
                elif c == '>':
                    angle -= 1
                elif c == '(':
                    paren += 1
                elif c == ')':
                    paren -= 1
                elif c == '[':
                    square += 1
                elif c == ']':
                    square -= 1
                elif c == '{' and angle == paren == square == 0:
                    body, brace = True, 1
                elif c == ';' and angle == paren == square == 0:
                    end = i + 1
                    break
        if end is None:
            raise ValueError(f'Unclosed {match[1]} at line {text.count(chr(10), 0, start) + 1}')
        header_end = re.search(r'[:<={;]', masked[match.end():end])
        name_end = match.end() + header_end.start() if header_end else end
        name = text[match.end():name_end].strip() or None
        if match[1] == 'defset':
            # defset has a typed header: defset list<Record> Group = {...}.
            typed = re.match(r'\s*list\s*<[^>]+>\s*([^=]+)=', masked[match.end():end])
            if not typed:
                raise ValueError('Unsupported defset header')
            name = typed[1].strip()
        records.append({'kind': match[1], 'name': name,
                        'line_start': text.count('\n', 0, start) + 1,
                        'line_end': text.count('\n', 0, end - 1) + 1,
                        'offset_start': start, 'offset_end': end,
                        'raw_text': text[start:end]})
    return records


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def build_catalog(source_root):
    root = Path(source_root).resolve()
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    if head != COMMIT:
        raise ValueError(f'Expected pinned commit {COMMIT}, found {head}')
    files, records = [], []
    for path in sorted((root / TARGET).glob('*.td')):
        if path.name in EXCLUDED:
            continue
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        pinned = git(root, 'show', f'{COMMIT}:{relative}')
        if raw != pinned:
            raise ValueError(f'Local source differs from pinned blob: {relative}')
        text = raw.decode('utf-8')
        found = extract_declarations(text)
        for record in found:
            record.update({'id': f"{relative}:{record['offset_start']}",
                           'source_path': relative,
                           'source_url': f"{BASE_URL}{relative}#L{record['line_start']}-L{record['line_end']}"})
        records.extend(found)
        files.append({'source_path': relative, 'sha256': hashlib.sha256(raw).hexdigest(),
                      'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
                      'byte_count': len(raw), 'line_count': len(text.splitlines()),
                      'record_count': len(found),
                      'source_url': f'{BASE_URL}{relative}#L1-L{len(text.splitlines())}',
                      'includes': re.findall(r'^\s*include\s+"([^"]+)"', text, re.M)})
    if not files:
        raise ValueError('No AIE2P source files found')
    return {'schema_version': 1, 'source_repository': 'https://github.com/Xilinx/llvm-aie',
            'source_commit': COMMIT, 'architecture': 'AIE2P (arch 21)', 'scope': SCOPE,
            'excluded_files': [f'{TARGET}/{name}' for name in sorted(EXCLUDED)],
            'counts': {'files': len(files), 'records': len(records),
                       'by_kind': dict(sorted(Counter(r['kind'] for r in records).items()))},
            'files': files, 'records': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'sources/llvm-aie')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    output = args.output.resolve()
    if output == source or source in output.parents:
        parser.error('Output must be outside the read-only source tree')
    catalog = build_catalog(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(catalog['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
