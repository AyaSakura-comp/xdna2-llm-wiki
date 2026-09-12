"""Narrow regressions for reviewed claims; reads pinned local Git objects only."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_COMMIT = "0ed8e7e477fd9094acee8dada7ab81604a7fb07a"
MODEL_PATH = "lib/Dialect/AIE/IR/AIETargetModel.cpp"
MODEL_URL = f"https://github.com/Xilinx/mlir-aie/blob/{MODEL_COMMIT}/{MODEL_PATH}"
SHIM_RULE = "Shim：West/North/East同向回接須同channel；South→South在channel範圍內可跨channel"
TRACE_RULE = "Trace可進FIFO/South，送East/West則限定dest0。"


def pinned_lines(repo, commit, path):
    return subprocess.check_output(
        ["git", "-C", str(ROOT / repo), "show", f"{commit}:{path}"], text=True
    ).splitlines()


class SpecClaims(unittest.TestCase):
    def setUp(self):
        self.composer = (ROOT / "wiki/compose_specs.py").read_text()
        self.articles = {
            a["slug"]: a
            for a in json.loads((ROOT / "wiki/content/spec-system.json").read_text())
        }

    def test_shim_statement(self):
        article = self.articles["interconnect"]
        for name, text in (("canonical", self.composer), ("generated", article["body"])):
            with self.subTest(location=name):
                self.assertIn(SHIM_RULE, text)
                self.assertNotIn("Shim：方向bundle同向須同channel", text)
                self.assertIn(TRACE_RULE, text)
                self.assertIn("#L1119-L1131", text)
        self.assertIn(MODEL_URL + "#L1119-L1131", article["body"])
        self.assertIn(MODEL_URL + "#L1119-L1131", [s["url"] for s in article["sources"]])

    def test_pinned_shim_south_counterexample_evidence(self):
        # Source-text checks, not execution of the C++ model or a silicon test.
        lines = pinned_lines("sources/mlir-aie", MODEL_COMMIT, MODEL_PATH)
        bounds = "\n".join(lines[1074:1079])
        self.assertIn("srcChan >= int(getNumSourceSwitchboxConnections", bounds)
        self.assertIn("dstChan >= int(getNumDestSwitchboxConnections", bounds)
        south = " ".join(" ".join(lines[1118:1123]).split())
        self.assertEqual(south, "if (isBundleInList(srcBundle, {WireBundle::FIFO, WireBundle::South})) return isBundleInList(dstBundle, {WireBundle::TileControl, WireBundle::FIFO, WireBundle::South, WireBundle::West, WireBundle::North, WireBundle::East});")
        others = "\n".join(lines[1123:1131])
        self.assertIn("{WireBundle::West, WireBundle::North, WireBundle::East}", others)
        self.assertIn("(srcBundle == dstBundle)", others)
        self.assertIn("(srcChan == dstChan)", others)
        # South source 0 -> destination 1 is unequal but in bounds (8 / 6).
        self.assertEqual([s.strip() for s in lines[980:982]],
                         ["case WireBundle::South:", "return 8;"])
        self.assertEqual([s.strip() for s in lines[907:909]],
                         ["case WireBundle::South:", "return 6;"])

    def test_perfmod_citation_includes_memory_counter_count(self):
        suffix = "driver/src/global/xaie2pgbl_reginit.c#L2467-L2536"
        self.assertIn("{G}#L2467-L2536", self.composer)
        self.assertNotIn("#L2474-L2536", self.composer)
        article = self.articles["events-debug"]
        self.assertIn(suffix, article["body"])
        self.assertTrue(any(s["url"].endswith(suffix) for s in article["sources"]))
        lines = pinned_lines("sources/mlir-aie/third_party/aie-rt",
                             "8849e208bdcc533b20a0ed3f95c1ce961dee9c3a",
                             "driver/src/global/xaie2pgbl_reginit.c")
        self.assertIn("static const XAie_PerfMod Aie2PTilePerfCnt[]", lines[2466])
        self.assertIn(".MaxCounterVal = 2U", lines[2468])

    def test_cycle_semantic_endpoint(self):
        path = "llvm/include/llvm/MC/MCInstrItineraries.h"
        lines = pinned_lines("sources/llvm-aie",
                             "386ca5c6634a84bb224b7248e79df8edabf0722f", path)
        self.assertEqual(len(lines), 262)
        extractor = (ROOT / "wiki/extract_schedule.py").read_text()
        self.assertIn(f'("{path}", 169, 262)', extractor)
        self.assertNotIn(f'("{path}", 169, 264)', extractor)
        cycles = (ROOT / "wiki/content/spec-cycles.json").read_text()
        self.assertIn("MCInstrItineraries.h#L169-L262", cycles)
        self.assertNotIn("MCInstrItineraries.h#L169-L264", cycles)
        audit = (ROOT / "notes/spec-cycle-audit.md").read_text()
        self.assertIn("MCInstrItineraries.h:169–262", audit)
        self.assertNotIn("MCInstrItineraries.h:169–264", audit)


if __name__ == "__main__":
    unittest.main()
