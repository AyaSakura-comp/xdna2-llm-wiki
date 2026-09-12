"""Read-only pinned-source audit; no TableGen/compiler/NPU execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("extract_schedule", ROOT / "wiki/extract_schedule.py")
extract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extract)


class ScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = extract.extract(ROOT / "sources/llvm-aie")
        cls.records = {r["name"]: r for r in cls.data["itineraries"]}

    def test_pin_and_reproducibility(self):
        self.assertEqual(self.data["source_commit"], "386ca5c6634a84bb224b7248e79df8edabf0722f")
        self.assertEqual(self.data, json.loads((ROOT / "wiki/spec-data/scheduling-model.json").read_text()))
        self.assertEqual(self.data["evidence_kind"], "compiler scheduling model; not measured silicon")
        self.assertNotIn("instruction_count", self.data["counts"])

    def test_full_model_coverage(self):
        paths = ["AIE2PGenSchedule.td", "ExtraItineraries.td"]
        raw = "\n".join((ROOT / "sources/llvm-aie/llvm/lib/Target/AIE/aie2p" / p).read_text() for p in paths)
        names = re.findall(r"\b(?:Mem)?InstrItinData\s*<\s*(\w+)", raw)
        self.assertEqual(sorted(names), sorted(r["name"] for r in self.data["itineraries"]))
        self.assertGreater(len(names), 1000)
        self.assertEqual(set(names), {d["name"] for d in self.data["declarations"]})
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(self.data["counts"]["raw_only_itineraries"], 0)
        self.assertTrue(all("raw" in r and "source" in r for r in self.data["definitions"]))

    def test_exact_ranges_and_hashes(self):
        cache = {}
        for source in self.data["source_files"]:
            content = extract.read_source(ROOT / "sources/llvm-aie", source["path"])
            self.assertEqual(hashlib.sha256(content.encode()).hexdigest(), source["sha256"])
            cache[source["path"]] = content
            self.assertNotIn("/aie2ps/", source["path"])
        for record in self.data["itineraries"] + self.data["definitions"] + self.data["declarations"]:
            s = record["source"]
            text = cache[s["path"]]
            self.assertEqual(text[s["start_offset"]:s["end_offset"]], record["raw"])
            self.assertEqual(text.count("\n", 0, s["start_offset"]) + 1, s["line_start"])
            self.assertEqual(text.count("\n", 0, s["end_offset"] - 1) + 1, s["line_end"])
            self.assertIn(self.data["source_commit"], s["url"])
            self.assertTrue(s["url"].endswith(f'#L{s["line_start"]}-L{s["line_end"]}'))

    def test_empty_resource_is_not_zero_instruction_latency(self):
        r = self.records["II_ABS"]["parsed"]
        self.assertEqual(r["stages"], [])
        self.assertEqual(r["operand_cycles"], [1, 1, 1])
        self.assertEqual(r["reservation_extent_cycles"], 0)
        self.assertNotIn("instruction_latency", r)

    def test_stage_overlap_delay_and_reservation(self):
        raw = "InstrItinData<II_TEST, [EmptyCycles<2>, PrefixCycle<A>, SimpleCycle<B>, IsPartWordStore, AvoidPartWordStore], [/*dst*/7, /*src*/1]>"
        r = extract.parse_itinerary(raw)["parsed"]
        self.assertEqual([s["start_cycle"] for s in r["stages"]], [0, 2, 2, 3, 3])
        self.assertEqual([s["cycles"] for s in r["stages"]], [0, 1, 1, 7, 1])
        self.assertEqual(r["stages"][-1]["kind"], "Reserved")
        self.assertEqual(r["reservation_extent_cycles"], 10)
        self.assertEqual(r["operand_labels"], ["dst", "src"])

    def test_unknown_complex_record_preserved(self):
        raw = "InstrItinData<II_COMPLEX, !listconcat(X, Y), [!add(2, 3)]>"
        r = extract.parse_itinerary(raw)
        self.assertEqual(r["raw"], raw)
        self.assertEqual(r["parse_status"], "raw_only")
        self.assertTrue(r["parse_notes"])
        self.assertIsNone(r["parsed"])

    def test_no_bypass_specializations_and_unequal_arrays(self):
        a = self.records["II_VEXP2"]["parsed"]
        b = self.records["II_VEXP2_eWHNoBypass"]["parsed"]
        self.assertEqual(a["bypasses"], ["MV_Bypass", "NoBypass"])
        self.assertEqual(b["bypasses"], ["NoBypass", "NoBypass"])
        self.assertEqual(a["operand_cycles"], [2, 1])
        r = self.records["II_VSUB_GE_16_vaddSign0"]["parsed"]
        self.assertEqual(len(r["operand_cycles"]), 5)
        self.assertEqual(len(r["bypasses"]), 4)  # do not invent explicit entries

    def test_memory_access_points_are_not_result_latency(self):
        r = self.records["II_LDA_3D_dms_lda"]["parsed"]
        self.assertEqual(r["memory_cycles"], [5])
        self.assertEqual(r["operand_cycles"][0], 7)
        self.assertEqual(self.data["counts"]["memory_itineraries"], 620)
        self.assertEqual(self.data["counts"]["itinerary_records"], 4013)
        self.assertTrue(any(len(x["parsed"]["memory_cycles"] or []) == 2 for x in self.data["itineraries"]))

    def test_model_constants_are_not_throughput(self):
        self.assertEqual(self.data["machine_model"]["values"]["IssueWidth"], 1000)
        self.assertEqual(self.data["machine_model"]["values"]["CompleteModel"], 0)
        self.assertGreater(len(self.data["composite_formats"]), 10)
        self.assertTrue(all(r["raw"] for r in self.data["composite_formats"]))

    def test_articles_schema_depth_and_inline_pin(self):
        records = json.loads((ROOT / "wiki/content/spec-cycles.json").read_text())
        self.assertEqual({r["slug"] for r in records}, {"instruction-cycles", "vliw-pipeline", "software-pipelining"})
        for r in records:
            self.assertTrue({"slug", "title", "summary", "category", "tags", "status", "body", "sources", "related"} <= r.keys())
            self.assertIn(r["category"], ["架構", "程式設計"])
            self.assertGreaterEqual(len(re.findall(r"^## ", r["body"], re.M)), 4)
            self.assertGreaterEqual(len(re.sub(r'https?://\S+', '', r["body"])), 800)
            self.assertIn("spec-data/scheduling-model.json", r["body"])
            self.assertGreaterEqual(r["body"].count(self.data["source_commit"]), 4)
            self.assertTrue({"isa", "compute", "mma", "performance", "compiler"} <= set(r["related"]))
            for s in r["sources"]:
                self.assertTrue({"label", "url", "note"} <= s.keys())
                self.assertIn(self.data["source_commit"], s["url"])
                self.assertNotIn("/aie2ps/", s["url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
