"""Publication regression guards from independently audited source contradictions.
These are wording guards, NOT proof of silicon or compiler capability.
"""
import unittest
from pathlib import Path
class Claims(unittest.TestCase):
    def test_source_contradictions_are_disclosed(self):
        text=(Path(__file__).resolve().parents[1]/'site/index.html').read_text()
        for claim in ['INT4：API 不等於原生指令','32×16 的 4×2×8 有直接 primitive','BFP8：本次未證實','AIE2P（arch 21）≠ AIE2PS（arch 22）','8 次 32-lane','每 8 個 signed 8-bit mantissa']:
            with self.subTest(claim=claim): self.assertIn(claim,text)
        self.assertNotIn('BFP8/混合 BFP 要查專用 kernel',text)
if __name__=='__main__': unittest.main()
