"""Unit tests for the ColorFrame Python reference implementation (TEST_PLAN.md section 3).

Rows passed to build_graphs are (line_number, [fields]) pairs, as produced by the TSV reader.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import colorframe as cf  # noqa: E402

LIMITS = cf.DEFAULT_LIMITS


def rows(*records):
    return [(i + 2, list(r)) for i, r in enumerate(records)]


def graph_of(nodes, edges=(), graph_id="G"):
    """nodes: (id, seq, colours-field); edges: (src, dst, overlap)."""
    node_rows = rows(*[(graph_id, n, s, c) for n, s, c in nodes])
    edge_rows = rows(*[(graph_id, a, b, str(o)) for a, b, o in edges])
    return cf.build_graphs(node_rows, edge_rows)[0]


def run(nodes, edges=(), policy="strict", **limits):
    return cf.search(graph_of(nodes, edges), policy, cf.DEFAULT_LIMITS._replace(**limits))


class ParsingTests(unittest.TestCase):
    def test_dna_accepts_upper_case_acgt(self):
        self.assertTrue(cf.is_valid_dna("ACGTTGCA"))

    def test_dna_rejects_empty_lowercase_and_other_letters(self):
        for bad in ("", "acgt", "ACGN", "AC GT", "ACGU"):
            self.assertFalse(cf.is_valid_dna(bad), bad)

    def test_identifier_pattern(self):
        for ok in ("n1", "A-b_c.9", "0"):
            self.assertTrue(cf.is_valid_id(ok), ok)
        for bad in ("", "a b", "a>b", "a\tb", "n#1", "é"):
            self.assertFalse(cf.is_valid_id(bad), bad)

    def test_colors_valid(self):
        self.assertEqual(cf.parse_colors("."), frozenset())
        self.assertEqual(cf.parse_colors("0"), frozenset({0}))
        self.assertEqual(cf.parse_colors("1,2,7"), frozenset({1, 2, 7}))
        self.assertEqual(cf.parse_colors("2147483647"), frozenset({2147483647}))

    def test_colors_invalid(self):
        for bad in ("", "2,1", "1,1", "01", "+1", "-1", "1,", ",1", "1x", "2147483648", "1, 2", ".,1"):
            with self.assertRaises(ValueError, msg=bad):
                cf.parse_colors(bad)

    def test_overlap_strict_integer(self):
        self.assertEqual(cf.parse_overlap("0"), 0)
        self.assertEqual(cf.parse_overlap("12"), 12)
        self.assertEqual(cf.parse_overlap("-3"), -3)
        self.assertEqual(cf.parse_overlap("-9223372036854775808"), -(2 ** 63))
        for bad in ("", "+1", "1x", "1.0", " 1", "9223372036854775808", "-9223372036854775809", "--1"):
            with self.assertRaises(ValueError, msg=bad):
                cf.parse_overlap(bad)


class ValidationTests(unittest.TestCase):
    def code_of(self, node_rows, edge_rows=()):
        with self.assertRaises(cf.ValidationError) as ctx:
            cf.build_graphs(rows(*node_rows), rows(*edge_rows))
        return ctx.exception.code

    def test_valid_graphs_sorted_by_graph_id(self):
        graphs = cf.build_graphs(rows(("B", "n", "ATG", "1"), ("A", "n", "ATG", "."),), [])
        self.assertEqual([g.graph_id for g in graphs], ["A", "B"])

    def test_node_errors(self):
        self.assertEqual(self.code_of([("G", "n", "ACGN", "1")]), "INVALID_DNA")
        self.assertEqual(self.code_of([("G", "n", "", "1")]), "INVALID_DNA")
        self.assertEqual(self.code_of([("G", "n", "acg", "1")]), "INVALID_DNA")
        self.assertEqual(self.code_of([("G", "n!", "ACG", "1")]), "INVALID_ID")
        self.assertEqual(self.code_of([("G", "n", "ACG", "2,1")]), "INVALID_COLORS")
        self.assertEqual(self.code_of([("G", "n", "ACG", "x")]), "INVALID_COLORS")
        self.assertEqual(self.code_of([("G", "n", "ACG", "1"), ("G", "n", "ACG", "1")]), "DUPLICATE_NODE")
        self.assertEqual(self.code_of([("G", "n", "ACG")]), "MALFORMED_INPUT")

    def test_same_node_id_in_different_graphs_is_fine(self):
        cf.build_graphs(rows(("A", "n", "ACG", "1"), ("B", "n", "ACG", "1")), [])

    def test_edge_errors(self):
        nodes = [("G", "a", "ACGT", "1"), ("G", "b", "GTAC", "1")]
        self.assertEqual(self.code_of(nodes, [("G", "a", "b")]), "MALFORMED_INPUT")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "x")]), "MALFORMED_INPUT")
        self.assertEqual(self.code_of(nodes, [("G", "a b", "b", "0")]), "INVALID_ID")
        self.assertEqual(self.code_of(nodes, [("G", "a", "zz", "0")]), "MISSING_NODE")
        self.assertEqual(self.code_of(nodes, [("Q", "a", "b", "0")]), "MISSING_NODE")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "0"), ("G", "a", "b", "0")]), "DUPLICATE_EDGE")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "-1")]), "INVALID_OVERLAP")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "5")]), "INVALID_OVERLAP")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "4")]), "INVALID_OVERLAP")
        self.assertEqual(self.code_of(nodes, [("G", "a", "b", "1")]), "OVERLAP_MISMATCH")

    def test_overlap_equal_to_source_length_is_allowed(self):
        # ov == len(source) is legal when the whole source is a prefix of the target.
        graph = graph_of([("a", "AC", "1"), ("b", "ACGT", "1")], [("a", "b", 2)])
        self.assertEqual(graph.overlap, 2)

    def test_inconsistent_overlap(self):
        nodes = [("G", "a", "AAAA", "1"), ("G", "b", "AAAA", "1"), ("G", "c", "AAAA", "1")]
        edges = [("G", "a", "b", "1"), ("G", "b", "c", "2")]
        self.assertEqual(self.code_of(nodes, edges), "INCONSISTENT_OVERLAP")

    def test_first_error_wins_node_row_order(self):
        # Row 2 has bad DNA, row 3 a bad id: the earlier row is reported.
        self.assertEqual(self.code_of([("G", "a", "ACGN", "1"), ("G", "b!", "ACG", "1")]), "INVALID_DNA")

    def test_error_message_names_file_line_and_value(self):
        with self.assertRaises(cf.ValidationError) as ctx:
            cf.build_graphs(rows(("G", "n", "ACGN", "1")), [])
        self.assertIn("nodes.tsv", ctx.exception.message)
        self.assertIn("line 2", ctx.exception.message)
        self.assertIn("ACGN", ctx.exception.message)

    def test_graph_without_edges_has_overlap_zero(self):
        self.assertEqual(graph_of([("a", "ATG", "1")]).overlap, 0)

    def test_nodes_indexed_in_sorted_id_order_with_sorted_successors(self):
        g = graph_of([("c", "AA", "1"), ("a", "AA", "1"), ("b", "AA", "1")],
                     [("a", "c", 0), ("a", "b", 0)])
        self.assertEqual(g.ids, ["a", "b", "c"])
        self.assertEqual(g.successors[0], [1, 2])


class RuleTests(unittest.TestCase):
    def test_colour_intersection(self):
        self.assertEqual(cf.intersect_colors(frozenset({1, 2}), frozenset({2, 3})), frozenset({2}))
        self.assertEqual(cf.intersect_colors(frozenset({1}), frozenset({2})), frozenset())
        self.assertEqual(cf.intersect_colors(frozenset(), frozenset({2})), frozenset())

    def test_start_frame_rule_prefix_of_atg(self):
        self.assertTrue(cf.can_start_frame("CCATGC", 2))   # full ATG
        self.assertTrue(cf.can_start_frame("CCAT", 2))     # AT at last-but-one position
        self.assertTrue(cf.can_start_frame("CCA", 2))      # A at the last position
        self.assertFalse(cf.can_start_frame("CCAT", 1))    # CAT
        self.assertFalse(cf.can_start_frame("ATC", 0))     # ATC is not a prefix of ATG
        self.assertFalse(cf.can_start_frame("AG", 0))
        self.assertFalse(cf.can_start_frame("CCT", 2))

    def test_stop_codon_detection(self):
        for stop in ("TAA", "TAG", "TGA"):
            self.assertTrue(cf.is_stop_codon(stop))
        for other in ("ATG", "TAC", "TTA", "AAA"):
            self.assertFalse(cf.is_stop_codon(other))

    def test_startable_range(self):
        self.assertEqual(cf.startable_end(10, False, 3), 10)  # no successors: whole node
        self.assertEqual(cf.startable_end(10, True, 3), 7)    # last K bases owned by successors
        self.assertEqual(cf.startable_end(10, True, 0), 10)


class SearchTests(unittest.TestCase):
    def test_single_node_orf_and_candidate_fields(self):
        res = run([("n1", "CCATGCCCGCCTAACC", "1")])
        self.assertEqual(len(res.candidates), 1)
        c = res.candidates[0]
        self.assertEqual((c.path, c.start_offset, c.length_nt, c.sequence), ("n1", 2, 12, "ATGCCCGCCTAA"))
        self.assertEqual((c.support_colors, c.status), ("1", "shared_support"))
        self.assertEqual(res.stats.search_states, 1)
        self.assertEqual(res.stats.candidates, 1)
        self.assertEqual(res.stats.max_depth, 1)
        self.assertEqual(res.duplicates_dropped, 0)

    def test_no_start_codon(self):
        res = run([("n1", "CCCGGGTTT", "1")])
        self.assertEqual(res.candidates, [])
        self.assertEqual(res.stats.search_states, 0)

    def test_dead_end_when_no_stop(self):
        res = run([("n1", "ATGCCC", "1")])
        self.assertEqual(res.candidates, [])
        self.assertEqual(res.stats.dead_ends, 1)

    def test_premature_in_frame_stop_ends_orf(self):
        res = run([("n1", "ATGCTAACCTAG", "1")])
        # ATG CTA ACC TAG: CTA/ACC are not stops, so the first in-frame stop is TAG.
        self.assertEqual([c.sequence for c in res.candidates], ["ATGCTAACCTAG"])

    def test_stop_must_be_in_frame(self):
        # ATG C TAA: TAA at offset 4 is out of frame; the ORF stays open.
        res = run([("n1", "ATGCTAAC", "1")])
        self.assertEqual(res.candidates, [])
        self.assertEqual(res.stats.dead_ends, 1)

    def test_start_codon_across_node_boundary(self):
        res = run([("n1", "CCCCAT", "1"), ("n2", "GCCCTGACC", "1")], [("n1", "n2", 0)])
        c = res.candidates[0]
        self.assertEqual((c.path, c.start_offset, c.sequence), ("n1>n2", 4, "ATGCCCTGA"))

    def test_start_frame_rejected_when_completed_codon_is_not_atg(self):
        res = run([("n1", "CCAT", "1"), ("n2", "CCC", "1")], [("n1", "n2", 0)])
        self.assertEqual(res.candidates, [])
        self.assertEqual(res.stats.start_rejected, 1)
        self.assertEqual(res.stats.search_states, 2)

    def test_frame_tracking_with_overlap_k3(self):
        nodes = [("n1", "CCATGCCG", "1,2"), ("n2", "CCGGCCGCC", "1,2"), ("n3", "GCCTAACC", "1")]
        res = run(nodes, [("n1", "n2", 3), ("n2", "n3", 3)])
        c = res.candidates[0]
        self.assertEqual((c.path, c.start_offset, c.length_nt, c.sequence),
                         ("n1>n2>n3", 2, 15, "ATGCCGGCCGCCTAA"))
        self.assertEqual(len(res.candidates), 1)

    def test_stop_codon_spanning_nodes_with_overlap_k1(self):
        res = run([("n1", "ATGCCA", "1"), ("n2", "ATAGCC", "1")], [("n1", "n2", 1)])
        self.assertEqual([(c.path, c.sequence) for c in res.candidates], [("n1>n2", "ATGCCATAG")])

    def test_start_position_ownership_in_overlap_region(self):
        # ATG sits in the K=3 overlap: only the downstream node owns that start.
        res = run([("n1", "CCCATG", "1"), ("n2", "ATGAAATAA", "1")], [("n1", "n2", 3)])
        self.assertEqual([(c.path, c.start_offset) for c in res.candidates], [("n2", 0)])

    def test_branching_explores_all_successors(self):
        nodes = [("n1", "ATGCCC", "1,2"), ("n2", "GCCTAACC", "1"), ("n3", "GGGCCCTGACC", "2")]
        res = run(nodes, [("n1", "n2", 0), ("n1", "n3", 0)])
        self.assertEqual([(c.path, c.support_colors) for c in res.candidates],
                         [("n1>n2", "1"), ("n1>n3", "2")])
        self.assertEqual(res.stats.search_states, 3)

    def test_strict_prunes_fragmented_support_permissive_reports_it(self):
        nodes = [("n1", "ATGCCC", "1"), ("n2", "GCCTAACC", "2")]
        edges = [("n1", "n2", 0)]
        strict = run(nodes, edges, "strict")
        self.assertEqual(strict.candidates, [])
        self.assertEqual(strict.stats.color_pruned, 1)
        perm = run(nodes, edges, "permissive")
        c = perm.candidates[0]
        self.assertEqual((c.support_colors, c.status), (".", "fragmented_support"))
        self.assertEqual(perm.stats.color_pruned, 0)

    def test_uncoloured_node_is_pruned_by_both_policies(self):
        res_s = run([("n1", "ATGTAA", ".")], policy="strict")
        res_p = run([("n1", "ATGTAA", ".")], policy="permissive")
        for res in (res_s, res_p):
            self.assertEqual(res.candidates, [])
            self.assertEqual(res.stats.color_pruned, 1)
            self.assertEqual(res.stats.search_states, 1)

    def test_cycle_terminates_through_node_visit_bound(self):
        # ATGC loops forever without a stop (frame shifts by 1 each lap).
        res = run([("n", "ATGC", "1")], [("n", "n", 0)])
        self.assertEqual(res.candidates, [])
        self.assertEqual(res.stats.search_states, 2)
        self.assertEqual(res.stats.max_depth, 2)
        self.assertEqual(res.stats.node_visit_cuts, 1)
        self.assertEqual(res.stats.exhaustive, 0)

    def test_bounded_revisit_respects_max_node_visits(self):
        res = run([("n", "ATGC", "1")], [("n", "n", 0)], max_node_visits=3)
        self.assertEqual(res.stats.search_states, 3)
        self.assertEqual(res.stats.node_visit_cuts, 1)
        res = run([("n", "ATGC", "1")], [("n", "n", 0)], max_node_visits=1)
        self.assertEqual(res.stats.search_states, 1)
        self.assertEqual(res.stats.node_visit_cuts, 1)

    def test_path_length_bound_takes_precedence(self):
        res = run([("n", "ATGC", "1")], [("n", "n", 0)], max_path_nodes=1, max_node_visits=1)
        self.assertEqual(res.stats.path_length_cuts, 1)
        self.assertEqual(res.stats.node_visit_cuts, 0)

    def test_state_limit_aborts_immediately(self):
        res = run([("n", "ATGC", "1")], [("n", "n", 0)], max_states=1)
        self.assertEqual(res.stats.search_states, 1)
        self.assertEqual(res.stats.state_limit_hit, 1)
        self.assertEqual(res.stats.exhaustive, 0)

    def test_candidates_before_state_limit_are_kept(self):
        nodes = [("a", "ATGTAA", "1"), ("b", "ATGTAA", "1")]
        res = run(nodes, max_states=1)
        self.assertEqual([c.path for c in res.candidates], ["a"])
        self.assertEqual(res.stats.state_limit_hit, 1)

    def test_orf_length_cut_and_boundary(self):
        res = run([("n", "ATGAAAAAA", "1")], max_orf_nt=6)
        self.assertEqual(res.stats.orf_length_cuts, 1)
        self.assertEqual(res.candidates, [])
        # A stop codon completed exactly at the limit is still a candidate.
        res = run([("n", "ATGTAA", "1")], max_orf_nt=6)
        self.assertEqual(len(res.candidates), 1)
        self.assertEqual(res.stats.orf_length_cuts, 0)

    def test_sequence_buffer_restored_on_backtrack(self):
        # Both branches must spell from the same prefix; a leaked buffer would corrupt n1>n3.
        nodes = [("n1", "ATGCCC", "1"), ("n2", "GGGGGG", "1"), ("n3", "GCCTAA", "1")]
        res = run(nodes, [("n1", "n2", 0), ("n1", "n3", 0)])
        self.assertEqual([(c.path, c.sequence) for c in res.candidates], [("n1>n3", "ATGCCCGCCTAA")])

    def test_exhaustive_flag(self):
        res = run([("n1", "ATGTAA", "1")])
        self.assertEqual(res.stats.exhaustive, 1)

    def test_empty_graph(self):
        graphs = cf.build_graphs([], [])
        self.assertEqual(graphs, [])


if __name__ == "__main__":
    unittest.main()
