#!/usr/bin/env python3
"""Read-only, stdlib-only extraction of the pinned AIE2P scheduling model.

Usage: python3 -B wiki/extract_schedule.py > wiki/spec-data/scheduling-model.json
Reads Git objects (including sparse-checkout omissions); never modifies sources,
executes TableGen, compiles, accesses a network, or installs anything. This is a
bounded literal parser, NOT a TableGen evaluator. Unsupported syntax stays raw.
Offsets are Unicode character offsets; line ranges are 1-based and inclusive.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

COMMIT = "386ca5c6634a84bb224b7248e79df8edabf0722f"
BASE = f"https://github.com/Xilinx/llvm-aie/blob/{COMMIT}/"
AIE = "llvm/lib/Target/AIE/"
P = AIE + "aie2p/"
MODEL_FILES = [P + f for f in ("AIE2PSchedule.td", "AIE2PGenSchedule.td", "ExtraItinDecls.td", "ExtraItineraries.td")]
FORMAT_FILES = [P + f for f in ("AIE2PSlots.td", "AIE2PSlotInclude.td", "AIE2PCompositeFormats.td", "AIE2PCompositeFormatsInclude.td")]
SEMANTIC_FILES = ["llvm/include/llvm/Target/AIETarget.td", "README.md", "llvm/include/llvm/Target/TargetItinerary.td", "llvm/include/llvm/Target/TargetSchedule.td", "llvm/include/llvm/MC/MCInstrItineraries.h", "llvm/utils/TableGen/SubtargetEmitter.cpp", AIE + "AIEHazardRecognizer.cpp", AIE + "AIEBaseInstrInfo.cpp", AIE + "AIEBaseInstrInfo.h", AIE + "AIEPostPipeliner.cpp", AIE + "AIEPostPipeliner.h", AIE + "AIEInterBlockScheduling.cpp", AIE + "AIEMachineScheduler.cpp", AIE + "MCTargetDesc/AIEMCFormats.cpp", P + "AIE2PInstrInfo.cpp", P + "AIE2PGenInstrInfo.td"]


def read_source(root, path):
    """Read the exact pinned object, not an unverified mutable worktree file."""
    return subprocess.check_output(["git", "-C", str(root), "show", f"{COMMIT}:{path}"]).decode("utf-8")


def masked(text):
    # Preserve every offset/newline while hiding comments and string contents.
    def blank(m):
        return "".join("\n" if c == "\n" else " " for c in m.group())
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"', blank, text)


def clean(text):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', text).strip()


def split_top(text):
    mask = masked(text)
    stack, out, begin = [], [], 0
    pairs = {">": "<", "]": "[", ")": "(", "}": "{"}
    for i, c in enumerate(mask):
        if c in "<[{(":
            stack.append(c)
        elif c in pairs:
            if not stack or stack.pop() != pairs[c]:
                raise ValueError("unbalanced expression")
        elif c == "," and not stack:
            out.append(text[begin:i].strip())
            begin = i + 1
    if stack:
        raise ValueError("unclosed expression")
    if text[begin:].strip():
        out.append(text[begin:].strip())
    return out


def list_items(text):
    text = text.strip()
    if not (text.startswith("[") and text.endswith("]")):
        raise ValueError("not a literal list")
    return split_top(text[1:-1])


def integer(text):
    text = clean(text)
    if not re.fullmatch(r"-?\d+", text):
        raise ValueError("not a literal integer: " + text)
    return int(text)


def symbols(text):
    vals = [clean(v) for v in list_items(text)]
    if not all(re.fullmatch(r"\w+", v) for v in vals):
        raise ValueError("not a literal symbol list")
    return vals


def stage(text):
    value = clean(text)
    aliases = {"IsPartWordStore": "InstrStage<7, [PART_WORD_STORE], 0>", "AvoidPartWordStore": "InstrStage<1, [PART_WORD_STORE], 0, Reserved>"}
    value = aliases.get(value, value)
    m = re.fullmatch(r"(\w+)\s*<([\s\S]*)>", value)
    if not m:
        raise ValueError("unsupported stage: " + value)
    name, args = m[1], split_top(m[2])
    if name == "EmptyCycles" and len(args) == 1:
        cycles, units, inc, kind = 0, ["EMPTY_FU"], integer(args[0]), "Required"
    elif name in ("SimpleCycle", "PrefixCycle") and len(args) == 1 and re.fullmatch(r"\w+", clean(args[0])):
        cycles, units, inc, kind = 1, [clean(args[0])], (0 if name == "PrefixCycle" else -1), "Required"
    elif name == "InstrStage" and 2 <= len(args) <= 4:
        cycles, units = integer(args[0]), symbols(args[1])
        inc = integer(args[2]) if len(args) > 2 else -1
        kind = clean(args[3]) if len(args) > 3 else "Required"
    else:
        raise ValueError("unsupported stage constructor: " + name)
    if cycles < 0 or inc < -1 or kind not in ("Required", "Reserved"):
        raise ValueError("unsupported stage values")
    # Multi-FU alternatives need the target's grouped-resource interpreter;
    # preserve raw rather than guess that the list means all or any units.
    if len(units) != 1:
        raise ValueError("multiple/empty FU list requires semantic evaluation")
    return dict(raw=text, cycles=cycles, units=units, time_inc=inc,
                next_cycles=cycles if inc == -1 else inc, kind=kind)


def parse_itinerary(raw):
    record = dict(raw=raw, parsed=None, parse_status="raw_only", parse_notes=[])
    try:
        text = raw.strip().rstrip(",;")
        m = re.fullmatch(r"((?:Mem)?InstrItinData)\s*<([\s\S]*)>", text)
        if not m:
            raise ValueError("not an itinerary expression")
        args = split_top(m[2])
        record["name"] = clean(args[0])
        record["constructor"] = m[1]
        memory_cycles = None
        if m[1] == "MemInstrItinData":
            if not 4 <= len(args) <= 6:
                raise ValueError("unsupported memory itinerary signature")
            mem = re.fullmatch(r"MemoryCycles\s*<([\s\S]*)>", args.pop(3))
            if not mem:
                raise ValueError("unsupported MemoryCycles expression")
            memory_cycles = [integer(c) for c in list_items(mem[1])]
            if not memory_cycles or any(c < 1 for c in memory_cycles):
                raise ValueError("memory cycles must be nonempty positive list")
        if not re.fullmatch(r"\w+", record["name"]) or not 2 <= len(args) <= 5:
            raise ValueError("unsupported itinerary signature")
        stages = [stage(s) for s in list_items(args[1])]
        cursor, extent = 0, 0
        for s in stages:
            s["start_cycle"] = cursor
            s["end_cycle_exclusive"] = cursor + s["cycles"]
            extent = max(extent, cursor + s["cycles"])
            cursor += s["next_cycles"]
        operands = list_items(args[2]) if len(args) > 2 else []
        labels = []
        for op in operands:
            label = re.search(r"/\*(.*?)\*/", op)
            labels.append(label[1].strip() if label else None)
        bypasses = symbols(args[3]) if len(args) > 3 else []
        record["parsed"] = dict(stages=stages, operand_cycles=[integer(o) for o in operands],
            operand_labels=labels, bypasses=bypasses,
            num_micro_ops=integer(args[4]) if len(args) > 4 else 1,
            num_micro_ops_explicit=len(args) > 4,
            memory_cycles=memory_cycles,
            first_memory_cycle=memory_cycles[0] if memory_cycles else None,
            last_memory_cycle=memory_cycles[-1] if memory_cycles else None,
            reservation_extent_cycles=extent)
        record["parse_status"] = "literal_fields"
        record["parse_notes"] = ["Operand labels are source comments, not independently resolved def/use roles.", "Bypass arrays retain original length; no instruction-wide data-ready latency is inferred."]
    except ValueError as exc:
        record["parse_notes"] = [str(exc)]
    return record


def source_range(path, text, start, end):
    first = text.count("\n", 0, start) + 1
    last = text.count("\n", 0, end - 1) + 1
    return dict(path=path, line_start=first, line_end=last, start_offset=start,
                end_offset=end, url=f"{BASE}{path}#L{first}-L{last}")


def expressions(text, keyword):
    """Balanced expressions; comments cannot truncate angle brackets."""
    mask = masked(text)
    for m in re.finditer(r"\b" + keyword + r"\s*<", mask):
        depth, end = 1, m.end()
        while end < len(mask) and depth:
            if mask[end] == "<": depth += 1
            elif mask[end] == ">": depth -= 1
            end += 1
        if depth:
            raise ValueError("unterminated " + keyword)
        yield m.start(), end


def definitions(path, text):
    mask = masked(text)
    for m in re.finditer(r"\b(def|class)\s+(\w+)", mask):
        stack, end = [], m.end()
        pairs = {">": "<", "]": "[", ")": "(", "}": "{"}
        while end < len(mask):
            c = mask[end]
            if c in "<[{(": stack.append(c)
            elif c in pairs:
                if not stack or stack.pop() != pairs[c]:
                    raise ValueError("unbalanced definition " + m[2])
                if c == "}" and not stack:
                    end += 1
                    if end < len(mask) and mask[end] == ";": end += 1
                    break
            elif c == ";" and not stack:
                end += 1
                break
            end += 1
        yield dict(name=m[2], kind=m[1], raw=text[m.start():end],
                   source=source_range(path, text, m.start(), end))


def extract(root):
    files = {p: read_source(root, p) for p in MODEL_FILES + FORMAT_FILES + SEMANTIC_FILES}
    # Guard all hard-coded convenience expansions against source changes.
    gen = clean(files[P + "AIE2PGenSchedule.td"])
    expected = ["class EmptyCycles<int n> : InstrStage<0, [EMPTY_FU], n>;", "class SimpleCycle<FuncUnit FU> : InstrStage<1, [FU]>;", "class PrefixCycle<FuncUnit FU> : InstrStage<1, [FU], 0>;", "def IsPartWordStore : InstrStage<7, [PART_WORD_STORE], 0>;", "def AvoidPartWordStore : InstrStage<1, [PART_WORD_STORE], 0, Reserved>;"]
    for expression in expected:
        if expression not in gen:
            raise ValueError("stage helper changed: " + expression)
    defs = [d for p in MODEL_FILES for d in definitions(p, files[p])]
    declarations = [d for d in defs if re.search(r":\s*InstrItinClass\s*;", d["raw"])]
    itineraries = []
    for p in MODEL_FILES:
        for start, end in expressions(files[p], "(?:Mem)?InstrItinData"):
            r = parse_itinerary(files[p][start:end])
            r["source"] = source_range(p, files[p], start, end)
            itineraries.append(r)
    model = next(d.copy() for d in defs if d["name"] == "AIE2PSchedModel")
    model["values"] = {m[1]: int(m[2]) for m in re.finditer(r"(?:int|let)\s+(\w+)\s*=\s*(-?\d+)\s*;", clean(model["raw"]))}
    format_defs = [d for p in FORMAT_FILES for d in definitions(p, files[p])]
    formats = [d.copy() for d in format_defs if d["kind"] == "def" and re.match(r"I\d+_", d["name"])]
    for d in formats:
        d["bits"] = int(re.match(r"I(\d+)_", d["name"])[1])
        d["slots"] = re.findall(r"(\w+)_slot\s*:\s*\$", d["raw"])
        d["parse_status"] = "literal_format_name_and_slot_operands; encoding retained raw"
    sources = []
    for p, text in files.items():
        data = text.encode()
        sources.append(dict(path=p, sha256=hashlib.sha256(data).hexdigest(),
            git_blob_sha1=hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
            bytes=len(data), lines=len(text.splitlines()), url=BASE+p,
            role="model" if p in MODEL_FILES else "format" if p in FORMAT_FILES else "semantic_reference"))
    evidence_ranges = [
        ("llvm/include/llvm/Target/TargetItinerary.td", 41, 120),
        ("llvm/include/llvm/Target/AIETarget.td", 22, 47),
        ("llvm/utils/TableGen/SubtargetEmitter.cpp", 355, 432),
        ("llvm/include/llvm/MC/MCInstrItineraries.h", 169, 262),
        (AIE + "AIEBaseInstrInfo.cpp", 892, 1024),
        (AIE + "AIEBaseInstrInfo.cpp", 1082, 1165),
        (AIE + "AIEHazardRecognizer.cpp", 133, 178),
        (AIE + "AIEHazardRecognizer.cpp", 575, 626),
        (AIE + "AIEHazardRecognizer.cpp", 714, 778),
        (AIE + "AIEPostPipeliner.cpp", 232, 251),
        (AIE + "AIEPostPipeliner.cpp", 466, 503),
    ]
    semantic_evidence = []
    for p, first, last in evidence_ranges:
        lines = files[p].splitlines(keepends=True)
        start = sum(map(len, lines[:first-1]))
        end = sum(map(len, lines[:last]))
        semantic_evidence.append(dict(raw=files[p][start:end], source=source_range(p, files[p], start, end)))
    counts = dict(model_definitions=len(defs), itinerary_declarations=len(declarations),
        itinerary_records=len(itineraries), memory_itineraries=sum(r.get("constructor") == "MemInstrItinData" for r in itineraries), literal_itineraries=sum(r["parsed"] is not None for r in itineraries),
        raw_only_itineraries=sum(r["parsed"] is None for r in itineraries),
        functional_unit_definitions=sum(bool(re.search(r":\s*FuncUnit\s*;", d["raw"])) for d in defs),
        bypass_definitions=sum(bool(re.search(r":\s*Bypass\s*;", d["raw"])) for d in defs),
        composite_formats=len(formats), source_files=len(sources),
        itineraries_by_file=dict(Counter(r["source"]["path"] for r in itineraries)))
    return dict(schema_version=1, source_commit=COMMIT, target="AIE2P / aie2p (not AIE2PS / aie2ps)",
        evidence_kind="compiler scheduling model; not measured silicon", source_files=sources,
        counts=counts, machine_model=model, definitions=defs, declarations=declarations,
        semantic_evidence=semantic_evidence,
        itineraries=itineraries, format_definitions=format_defs, composite_formats=formats,
        semantics={
            "scope": "All literal def/class, InstrItinData and MemInstrItinData records in AIE2PSchedule.td, AIE2PGenSchedule.td and both local Extra* includes; no TableGen expansion or opcode counting.",
            "memory_cycles": "MemInstrItinData extends InstrItinData with MemoryCycles, not an extra bypass list. Source access points are 1-based; scoreboard subtracts 1. First/last are first/last list values, including read-modify-write lists. They are neither result-ready latency nor lock wait duration.",
            "stage_cycles": "Reservation duration. Starts at offset 0; advance by TimeInc (default -1 resolves to Cycles). PrefixCycle overlaps next stage; EmptyCycles reserves nothing and advances time.",
            "reservation_extent_cycles": "max(start_cycle + cycles), initially zero. A resource-table envelope, NOT data-ready latency; no-stages means no listed FU use, NOT a zero-cycle instruction.",
            "operand_cycles": "Ordered source operand read/write points after issue. Labels are comments. Need actual instruction def/use ordering, implicit operands, resolved schedule class and consumer to derive an edge.",
            "bypasses": "Raw list, potentially shorter than operand cycles; TableGen emitter pads omitted entries with zero forwarding. NoBypass is distinct from MV_Bypass/VEC_Bypass. AIE target hook, not generic one-cycle assumption, controls benefit.",
            "RAW": "AIEBaseInstrInfo signed edge = producer write cycle - consumer read cycle + 1 - getNumBypassedCycles(...); unsigned getOperandLatency caps negatives at zero.",
            "WAR_WAW": "WAR = earlier read cycle - later write cycle after reverse-bypass adjustment (no +1); WAW = earlier write - later write +1. These are dependency edge constraints, not elapsed execution times.",
            "resources": "Required/Required and Required/Reserved conflict; Reserved/Reserved alone does not. No silicon stage name, physical-unit census or inter-tile hop latency inferred from FU names.",
            "issue": "IssueWidth=1000 and MicroOpBufferSize=1000 are scheduling controls, not 1000-wide issue/physical ROB; slot, conflict, legal format and scoreboard restrictions still apply.",
            "limits": "No complete TableGen evaluation, instruction lowering, assembled bundles, simulator or silicon measurement. Raw-only records are preserved if literal interpretation fails. CompleteModel=0 and FIXME constants remain explicit. No inference that schedule-class count equals instruction count."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1] / "sources/llvm-aie")
    args = parser.parse_args()
    json.dump(extract(args.source_root), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
