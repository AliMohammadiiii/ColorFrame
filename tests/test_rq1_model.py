#!/usr/bin/env python3
"""RQ1 model and evaluation tests (v1.0.1, D-021).

Evidence accounting must use each planted ORF's true sample set; spurious colours are an explicit,
separately seeded process; replicates are deterministic and paired across p and noise.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
import evaluate_rq1 as ev  # noqa: E402
import generate_workloads as gw  # noqa: E402

T = {1, 2}  # true samples used in the hand-made cases


class SupportFlags(unittest.TestCase):
    def flags(self, *colours):
        return ev.support_flags([set(c) for c in colours], T)

    def test_fully_true_supported(self):
        f = self.flags({1}, {1, 2}, {1})
        self.assertTrue(f["true_local"] and f["true_shared"])
        self.assertFalse(f["spurious_local_only"] or f["spurious_shared_only"])

    def test_complementary_true_local_without_true_shared(self):
        f = self.flags({1}, {2}, {1})
        self.assertTrue(f["true_local"])
        self.assertFalse(f["true_shared"])
        self.assertFalse(f["all_shared"])

    def test_spurious_only(self):
        f = self.flags({7}, {7}, {7})
        self.assertTrue(f["all_local"] and f["all_shared"])
        self.assertFalse(f["true_local"] or f["true_shared"])
        self.assertTrue(f["spurious_local_only"] and f["spurious_shared_only"])

    def test_neither_true_nor_spurious(self):
        f = self.flags({1}, set(), {1})
        self.assertFalse(f["all_local"] or f["true_local"] or f["all_shared"] or f["true_shared"])
        self.assertFalse(f["spurious_local_only"] or f["spurious_shared_only"])

    def test_mixture_true_local_but_spurious_shared(self):
        # true local support exists, but the only colour shared by every node is spurious (7)
        f = self.flags({1, 7}, {2, 7}, {1, 7})
        self.assertTrue(f["true_local"])
        self.assertFalse(f["true_shared"])
        self.assertTrue(f["all_shared"])
        self.assertTrue(f["spurious_shared_only"])
        self.assertFalse(f["spurious_local_only"])

    def test_spurious_local_only_means_some_node_lacks_true_support(self):
        # Nodes 1 and 3 carry a true sample; node 2 carries only a non-true colour. The flag is
        # set although most of the path has true evidence: it means "local support exists, but
        # at least one node lacks true-sample support", NOT "supported only by spurious colours".
        f = self.flags({1}, {7}, {1})
        self.assertTrue(f["all_local"])
        self.assertFalse(f["true_local"])
        self.assertTrue(f["spurious_local_only"])

    def test_strict_can_pass_on_shared_non_true_colour(self):
        # True samples cover every node but no single true sample spans the path, while the
        # non-true colour 7 does: strict support exists without the true shared criterion.
        f = self.flags({1, 7}, {2, 7}, {1, 7})
        self.assertTrue(f["all_shared"] and f["spurious_shared_only"])
        self.assertFalse(ev.policy_ceiling("strict", f))

    def test_policy_specific_ceilings(self):
        f = self.flags({1}, {2}, {1})
        self.assertFalse(ev.policy_ceiling("strict", f))
        self.assertTrue(ev.policy_ceiling("permissive", f))


class Rq1Generator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def gen(self, rep, p, cond, sub):
        out = self.root / sub
        gw.build_rq1(rep, p, cond, out_root=out)
        return out / gw.rq1_name(rep, p, cond)

    def read(self, d, f):
        return (d / f).read_text()

    def colours(self, d):
        rows = [l.split("\t") for l in self.read(d, "nodes.tsv").splitlines()[1:]]
        return {r[1]: (set() if r[3] == "." else set(map(int, r[3].split(",")))) for r in rows}

    def test_deterministic_replication(self):
        a, b = self.gen(3, 0.3, "noisy", "a"), self.gen(3, 0.3, "noisy", "b")
        for f in ("nodes.tsv", "edges.tsv", "planted.tsv", "params.json"):
            self.assertEqual(self.read(a, f), self.read(b, f), f)

    def test_paired_design_fixes_structure_within_replicate(self):
        base = self.gen(0, 0.3, "clean", "x")
        seqs = lambda d: [l.split("\t")[2] for l in self.read(d, "nodes.tsv").splitlines()[1:]]
        for p, cond in ((0.7, "clean"), (0.3, "noisy"), (0.9, "noisy")):
            other = self.gen(0, p, cond, f"x{p}{cond}")
            self.assertEqual(self.read(base, "edges.tsv").split("\n", 1)[1].replace(base.name, ""),
                             self.read(other, "edges.tsv").split("\n", 1)[1].replace(other.name, ""))
            self.assertEqual(seqs(base), seqs(other))
            self.assertEqual(self.read(base, "planted.tsv"), self.read(other, "planted.tsv"))
        self.assertNotEqual(seqs(base), seqs(self.gen(1, 0.3, "clean", "rep1")))  # replicates differ

    def test_zero_noise_condition_uses_only_true_samples_on_planted_nodes(self):
        d = self.gen(0, 0.7, "clean", "c")
        col = self.colours(d)
        params = json.loads(self.read(d, "params.json"))
        self.assertEqual(params["p_spurious_colour"], 0.0)
        for line in self.read(d, "planted.tsv").splitlines()[1:]:
            path, _, _, _, true = line.split("\t")
            truth = set(map(int, true.split(",")))
            for v in path.split(">"):
                self.assertLessEqual(col[v], truth)

    def test_noisy_condition_adds_only_non_true_colours(self):
        clean, noisy = self.gen(2, 0.5, "clean", "c"), self.gen(2, 0.5, "noisy", "n")
        cc, cn = self.colours(clean), self.colours(noisy)
        params = json.loads(self.read(noisy, "params.json"))
        self.assertAlmostEqual(params["p_spurious_colour"], 0.125)
        for v in cc:
            self.assertLessEqual(cc[v], cn[v])                       # noise only adds
        for line in self.read(noisy, "planted.tsv").splitlines()[1:]:
            path, _, _, _, true = line.split("\t")
            truth = set(map(int, true.split(",")))
            for v in path.split(">"):
                self.assertEqual(cn[v] & truth, cc[v] & truth)      # true observations unchanged

    def test_params_record_seeds_and_realised_support(self):
        params = json.loads(self.read(self.gen(4, 0.2, "noisy", "p"), "params.json"))
        for key in ("replicate", "p_true_observation", "p_spurious_colour", "condition",
                    "seed_structure", "seed_observation", "seed_spurious", "planted",
                    "realised_true_local_support", "realised_true_shared_support"):
            self.assertIn(key, params)


class EndToEndCeilings(unittest.TestCase):
    """Hand-made workload: planted n1>n2>n3 with true samples {1,2} and colours {1},{1,2},{2}."""

    def test_recovery_against_policy_ceilings(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "rq1_handmade"
            d.mkdir()
            (d / "nodes.tsv").write_text("graph_id\tnode_id\tsequence\tcolors\n"
                                         "g\tn1\tATGCCC\t1\ng\tn2\tGCCGCC\t1,2\ng\tn3\tTAACC\t2\n")
            (d / "edges.tsv").write_text("graph_id\tsource\ttarget\toverlap_nt\n"
                                         "g\tn1\tn2\t0\ng\tn2\tn3\t0\n")
            (d / "planted.tsv").write_text("path\tstart_offset\tlength_nt\tsequence\ttrue_samples\n"
                                           "n1>n2>n3\t0\t15\tATGCCCGCCGCCTAA\t1,2\n")
            (d / "params.json").write_text(json.dumps({"cli_args": "--policy both"}))
            rows = {r["policy"]: r for r in ev.evaluate(d, "python")}
        s, p = rows["strict"], rows["permissive"]
        self.assertEqual((s["true_ceiling"], s["recovered"], s["recovered_within_true_ceiling"]), (0, 0, 0))
        self.assertEqual((p["true_ceiling"], p["recovered"], p["recovered_within_true_ceiling"]), (1, 1, 1))
        self.assertEqual(p["true_local_support"], 1)
        self.assertEqual(p["true_shared_support"], 0)


if __name__ == "__main__":
    unittest.main()
