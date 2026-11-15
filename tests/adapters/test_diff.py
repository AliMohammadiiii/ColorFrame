#!/usr/bin/env python3
"""Difference classification for the ECOR identity diagnostic (no network)."""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from adapters import diff  # noqa: E402

T = "ACGTAAAAACGTCCGT"   # target; homopolymer AAAAA at 4-8 (0-based)


class Cs(unittest.TestCase):
    def test_mismatch_and_homopolymer_indels(self):
        # match 2, mismatch g->t at 2, match 2, delete one A inside the A-run at 5, match 4, insert C after 10
        ev = diff.parse_cs(":2*gt:2-a:4+c:5", T, 0)
        kinds = [(e["type"], e["pos"], e["homopolymer"]) for e in ev]
        self.assertEqual(kinds, [("mismatch", 2, False), ("deletion", 5, True), ("insertion", 10, False)])

    def test_summary(self):
        s = diff.summarise(diff.parse_cs(":2*gt:2-a:4+c:5", T, 0))
        self.assertEqual((s["mismatches"], s["insertions"], s["deletions"], s["indels_homopolymer"]), (1, 1, 1, 1))


class Vcf(unittest.TestCase):
    VCF = ("##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\ts\n"
           "c\t3\t.\tG\tT\t200\t.\t.\tGT\t1\n"          # SNP
           "c\t5\t.\tTA\tT\t200\t.\t.\tGT\t1\n"         # deletion of A in the A-run (1-based POS 5 = T)
           "c\t12\t.\tT\tTG\t10\t.\t.\tGT\t1\n"         # low quality: ignored
           "c\t14\t.\tC\tA\t200\t.\t.\tGT\t0\n")        # reference genotype: ignored

    def test_counts_only_confident_alt_calls(self):
        s = diff.vcf_summary(io.StringIO(self.VCF), {"c": T}, min_qual=30)
        self.assertEqual((s["snps"], s["indels"], s["indels_homopolymer"]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
