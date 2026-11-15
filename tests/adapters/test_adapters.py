#!/usr/bin/env python3
"""Adapter tests (biological-validation pilot). Standard library only; no network."""
import gzip
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from adapters import cds, fetch, identity, pilot_files  # noqa: E402

PILOT = ROOT / "docs" / "biological_validation" / "pilot_files.tsv"


class PilotFiles(unittest.TestCase):
    def test_committed_pilot_list_is_valid(self):
        rows = pilot_files.load(PILOT)
        reads = [r for r in rows if r["kind"] == "reads"]
        self.assertEqual(len(reads), 16)                                   # 8 ECOR + 8 de Bourcy
        self.assertEqual(sum(int(r["bytes"]) for r in reads), 905_242_623 + 928_043_766)
        self.assertEqual(len({r["dest"] for r in rows}), len(rows))        # unique destinations

    def test_rejects_bad_md5(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "f.tsv"
            p.write_text("dataset\tsample_id\tkind\turl\tbytes\tmd5\tdest\n"
                         "ecor\tECOR01\treads\thttps://x/a.fastq.gz\t10\tnot-an-md5\tecor/a.fastq.gz\n")
            with self.assertRaises(ValueError):
                pilot_files.load(p)


class Fetch(unittest.TestCase):
    def test_md5_mismatch_aborts_and_leaves_no_file(self):
        with tempfile.TemporaryDirectory() as t:
            row = {"url": "mem://x", "md5": "0" * 32, "dest": "d/x.bin", "bytes": "5"}
            with self.assertRaises(fetch.ChecksumError):
                fetch.fetch(row, Path(t), opener=lambda url: io.BytesIO(b"hello"))
            self.assertFalse((Path(t) / "d/x.bin").exists())

    def test_good_download_records_sha256(self):
        with tempfile.TemporaryDirectory() as t:
            data = b"hello"
            row = {"url": "mem://x", "md5": hashlib.md5(data).hexdigest(), "dest": "d/x.bin", "bytes": "5"}
            rec = fetch.fetch(row, Path(t), opener=lambda url: io.BytesIO(data))
            self.assertEqual((Path(t) / "d/x.bin").read_bytes(), data)
            self.assertEqual(rec["sha256"], hashlib.sha256(data).hexdigest())

    def test_size_mismatch_aborts(self):
        with tempfile.TemporaryDirectory() as t:
            data = b"hello"
            row = {"url": "mem://x", "md5": hashlib.md5(data).hexdigest(), "dest": "x", "bytes": "6"}
            with self.assertRaises(fetch.ChecksumError):
                fetch.fetch(row, Path(t), opener=lambda url: io.BytesIO(data))

    def test_fastq_stats(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "r.fastq.gz"
            with gzip.open(p, "wt") as f:
                f.write("@r1\nACGT\n+\nIIII\n@r2\nACGTAC\n+\nIIIIII\n")
            self.assertEqual(fetch.fastq_stats(p), {"reads": 2, "bases": 10, "max_len": 6})


# genome: contig c1 (24 nt) holds +strand ATG...TAA at 1-9, -strand CDS at 13-21, GTG start at 22-24 region
SEQ = "ATGAAATAA" + "CCC" + "TTACCCCAT" + "GTG"
#      1-9 (+)      10-12   13-21 (-) revcomp = ATGGGGTAA   22-24
def gff(lines):
    return "##gff-version 3\n" + "".join("c1\tX\tCDS\t" + l + "\n" for l in lines)


class CdsEligibility(unittest.TestCase):
    def classify(self, line, **kw):
        recs = cds.parse_gff3(io.StringIO(gff([line])))
        return cds.classify(recs[0], {"c1": SEQ}, **kw)

    def test_plus_strand_atg_eligible(self):
        self.assertEqual(self.classify("1\t9\t.\t+\t0\tID=a")["eligible"], True)

    def test_minus_strand_eligible_with_doubling_excluded_without(self):
        self.assertTrue(self.classify("13\t21\t.\t-\t0\tID=b", both_strands=True)["eligible"])
        r = self.classify("13\t21\t.\t-\t0\tID=b", both_strands=False)
        self.assertEqual((r["eligible"], r["exclusion_reason"]), (False, "strand"))

    def test_alt_start(self):
        recs = cds.parse_gff3(io.StringIO(gff(["1\t9\t.\t+\t0\tID=c"])))
        r = cds.classify(recs[0], {"c1": "GTGAAATAA" + SEQ[9:]})
        self.assertEqual((r["eligible"], r["exclusion_reason"], r["start_codon"]), (False, "alt_start", "GTG"))

    def test_pseudo_and_partial_take_precedence(self):
        self.assertEqual(self.classify("1\t9\t.\t+\t0\tID=d;pseudo=true")["exclusion_reason"], "pseudo")
        self.assertEqual(self.classify("1\t9\t.\t+\t0\tID=e;partial=true")["exclusion_reason"], "partial")

    def test_length_limit(self):
        r = self.classify("1\t9\t.\t+\t0\tID=f", max_orf_nt=6)
        self.assertEqual(r["exclusion_reason"], "length")

    def test_internal_stop(self):
        recs = cds.parse_gff3(io.StringIO(gff(["1\t9\t.\t+\t0\tID=g"])))
        r = cds.classify(recs[0], {"c1": "ATGTAATAA" + SEQ[9:]})
        self.assertEqual(r["exclusion_reason"], "internal_stop")

    def test_multi_segment_cds_joined_by_id(self):
        recs = cds.parse_gff3(io.StringIO(gff(["1\t3\t.\t+\t0\tID=h", "4\t9\t.\t+\t0\tID=h"])))
        self.assertEqual(len(recs), 1)
        self.assertEqual(cds.classify(recs[0], {"c1": SEQ})["length_nt"], 9)

    def test_summary_counts_sum_to_total(self):
        recs = cds.parse_gff3(io.StringIO(gff(["1\t9\t.\t+\t0\tID=a", "13\t21\t.\t-\t0\tID=b",
                                               "1\t9\t.\t+\t0\tID=d;pseudo=true"])))
        s = cds.summarise([cds.classify(r, {"c1": SEQ}, both_strands=False) for r in recs])
        self.assertEqual(s["total"], 3)
        self.assertEqual(s["eligible"] + sum(v for k, v in s.items() if k.startswith("excluded_")), 3)


class IdentityGate(unittest.TestCase):
    PAF = ("q1\t1000\t0\t1000\t+\tt\t5000\t0\t1000\t999\t1000\t60\ttp:A:P\n"
           "q2\t500\t0\t400\t+\tt\t5000\t2000\t2400\t400\t400\t60\ttp:A:P\n"
           "q2\t500\t100\t300\t+\tt\t5000\t3000\t3200\t200\t200\t5\ttp:A:S\n")

    def test_identity_and_aligned_fraction(self):
        r = identity.from_paf(io.StringIO(self.PAF))
        self.assertAlmostEqual(r["identity"], 1399 / 1400)
        self.assertAlmostEqual(r["aligned_fraction"], 1400 / 1500)        # secondary ignored

    def test_gate(self):
        self.assertTrue(identity.passes({"identity": 0.9995, "aligned_fraction": 0.99}))
        self.assertFalse(identity.passes({"identity": 0.998, "aligned_fraction": 0.99}))
        self.assertFalse(identity.passes({"identity": 0.9995, "aligned_fraction": 0.95}))


if __name__ == "__main__":
    unittest.main()
