// Minimal unit tests (standard library only). Topics follow TEST_PLAN.md section 3.
#include <iostream>
#include <string>
#include <vector>

#include "colorframe.hpp"

using namespace cf;

static int g_checks = 0, g_failures = 0;

#define CHECK(cond)                                                              \
    do {                                                                         \
        ++g_checks;                                                              \
        if (!(cond)) {                                                           \
            ++g_failures;                                                        \
            std::cerr << __FILE__ << ":" << __LINE__ << ": CHECK failed: " #cond "\n"; \
        }                                                                        \
    } while (0)

#define CHECK_EQ(a, b) CHECK((a) == (b))

// ---- helpers ---------------------------------------------------------------
static const char* NODES_HDR = "graph_id\tnode_id\tsequence\tcolors\n";
static const char* EDGES_HDR = "graph_id\tsource\ttarget\toverlap_nt\n";

static std::vector<Graph> build(const std::string& nodes_body, const std::string& edges_body) {
    return build_graphs(parse_table(NODES_HDR + nodes_body, "nodes.tsv"),
                        parse_table(EDGES_HDR + edges_body, "edges.tsv"));
}

// Returns the error code thrown by build(), or "" if the input was accepted.
static std::string build_code(const std::string& nodes_body, const std::string& edges_body) {
    try {
        build(nodes_body, edges_body);
    } catch (const ValidationError& e) {
        return e.code;
    }
    return "";
}

static SearchResult search(const std::string& nodes_body, const std::string& edges_body,
                           Policy p = Policy::Strict, Limits lim = Limits()) {
    return search_graph(build(nodes_body, edges_body).at(0), p, lim);
}

static std::vector<std::string> paths(const SearchResult& r) {
    std::vector<std::string> v;
    for (const auto& c : r.candidates) v.push_back(c.path);
    return v;
}

// ---- parsing and validation ------------------------------------------------
static void test_dna_validation() {
    CHECK(is_valid_dna("ACGT"));
    CHECK(is_valid_dna("A"));
    CHECK(!is_valid_dna(""));
    CHECK(!is_valid_dna("ACGN"));
    CHECK(!is_valid_dna("acgt"));
    CHECK(!is_valid_dna("AC GT"));
    CHECK_EQ(build_code("g\tn\tATGNCC\t1\n", ""), "INVALID_DNA");
    CHECK_EQ(build_code("g\tn\t\t1\n", ""), "INVALID_DNA");
}

static void test_id_validation() {
    CHECK(is_valid_id("n1"));
    CHECK(is_valid_id("Graph_1.a-b"));
    CHECK(!is_valid_id(""));
    CHECK(!is_valid_id("n>1"));
    CHECK(!is_valid_id("n 1"));
    CHECK_EQ(build_code("g\tn>1\tATG\t1\n", ""), "INVALID_ID");
    CHECK_EQ(build_code("g\tn1\tATG\t1\n", "g\tn1\tn>2\t0\n"), "INVALID_ID");
}

static void test_color_parsing() {
    std::vector<uint32_t> c;
    CHECK(parse_colors(".", c) && c.empty());
    CHECK(parse_colors("0", c) && c == std::vector<uint32_t>({0}));
    CHECK(parse_colors("1,2,7", c) && c == std::vector<uint32_t>({1, 2, 7}));
    CHECK(parse_colors("2147483647", c) && c == std::vector<uint32_t>({2147483647u}));
    CHECK(!parse_colors("2,1", c));
    CHECK(!parse_colors("1,1", c));
    CHECK(!parse_colors("1,x", c));
    CHECK(!parse_colors("01", c));
    CHECK(!parse_colors("+1", c));
    CHECK(!parse_colors("-1", c));
    CHECK(!parse_colors("", c));
    CHECK(!parse_colors("1,", c));
    CHECK(!parse_colors("2147483648", c));
    CHECK(!parse_colors("99999999999999999999", c));
    CHECK_EQ(build_code("g\tn\tATG\t2,1\n", ""), "INVALID_COLORS");
    CHECK_EQ(build_code("g\tn\tATG\t1,x\n", ""), "INVALID_COLORS");
}

static void test_int_parsing() {
    int64_t v = 0;
    CHECK(parse_int64("0", v) && v == 0);
    CHECK(parse_int64("-3", v) && v == -3);
    CHECK(parse_int64("9223372036854775807", v));
    CHECK(!parse_int64("9223372036854775808", v));
    CHECK(!parse_int64("x", v));
    CHECK(!parse_int64("+1", v));
    CHECK(!parse_int64("1x", v));
    CHECK(!parse_int64("", v));
    CHECK(!parse_int64("-", v));
}

static void test_table_and_headers() {
    Table t = parse_table("a\tb\n1\t2\n", "x");
    CHECK_EQ(t.rows.size(), 2u);
    CHECK_EQ(t.rows[1][1], "2");
    CHECK_EQ(parse_table("a\tb\n1\t2", "x").rows.size(), 2u);  // trailing newline optional
    // wrong header, wrong field count and blank line are MALFORMED_INPUT
    CHECK_EQ(build_code("", ""), "");
    try {
        build_graphs(parse_table("graph_id\tnode\n", "nodes.tsv"),
                     parse_table(EDGES_HDR, "edges.tsv"));
        CHECK(false);
    } catch (const ValidationError& e) {
        CHECK_EQ(e.code, "MALFORMED_INPUT");
    }
    CHECK_EQ(build_code("g\tn\tATG\n", ""), "MALFORMED_INPUT");
    CHECK_EQ(build_code("g\tn\tATG\t1\n\ng\tm\tATG\t1\n", ""), "MALFORMED_INPUT");
    CHECK_EQ(build_code("g\tn\tATG\t1\n", "g\tn\tn\tx\n"), "MALFORMED_INPUT");
    CHECK_EQ(build_code("g\tn\tATG\t1\n", "g\tn\tn\t99999999999999999999\n"), "MALFORMED_INPUT");
}

static void test_graph_construction() {
    // nodes given out of order; graphs sorted by id, nodes by id, successors by target id
    auto gs = build("b\tx\tATG\t1\n"
                    "a\tn2\tCCCC\t.\n"
                    "a\tn1\tCCCC\t1,2\n"
                    "a\tn3\tCCCC\t3\n",
                    "a\tn1\tn3\t1\n"
                    "a\tn1\tn2\t1\n");
    CHECK_EQ(gs.size(), 2u);
    CHECK_EQ(gs[0].id, "a");
    CHECK_EQ(gs[1].id, "b");
    CHECK_EQ(gs[0].nodes[0].id, "n1");
    CHECK_EQ(gs[0].nodes[2].id, "n3");
    CHECK(gs[0].nodes[0].colors == std::vector<uint32_t>({1, 2}));
    CHECK(gs[0].nodes[1].colors.empty());
    CHECK(gs[0].succ[0] == std::vector<int>({1, 2}));
    CHECK_EQ(gs[0].overlap, 1);
    CHECK_EQ(gs[1].overlap, 0);
    CHECK_EQ(build_code("g\tn\tATG\t1\ng\tn\tCCC\t1\n", ""), "DUPLICATE_NODE");
    // same node id in different graphs is fine
    CHECK_EQ(build_code("g\tn\tATG\t1\nh\tn\tCCC\t1\n", ""), "");
}

static void test_overlap_validation() {
    const std::string nodes = "g\ta\tATGCCC\t1\ng\tb\tCCGGGT\t1\n";
    CHECK_EQ(build_code(nodes, "g\ta\tb\t0\n"), "");
    CHECK_EQ(build_code(nodes, "g\ta\tz\t0\n"), "MISSING_NODE");   // unknown node
    CHECK_EQ(build_code(nodes, "h\ta\tb\t0\n"), "MISSING_NODE");   // unknown graph
    CHECK_EQ(build_code(nodes, "g\ta\tb\t0\ng\ta\tb\t0\n"), "DUPLICATE_EDGE");
    CHECK_EQ(build_code(nodes, "g\ta\tb\t-1\n"), "INVALID_OVERLAP");
    CHECK_EQ(build_code(nodes, "g\ta\tb\t7\n"), "INVALID_OVERLAP");  // > len(source)
    CHECK_EQ(build_code("g\ta\tATGCCC\t1\ng\tb\tCCC\t1\n", "g\ta\tb\t3\n"),
             "INVALID_OVERLAP");  // == len(target)
}

static void test_overlap_mismatch_and_consistency() {
    // suffix CC of a == prefix CC of b
    CHECK_EQ(build_code("g\ta\tATGCCC\t1\ng\tb\tCCGGGT\t1\n", "g\ta\tb\t2\n"), "");
    // suffix CC != prefix GG
    CHECK_EQ(build_code("g\ta\tATGCCC\t1\ng\tb\tGGGTAA\t1\n", "g\ta\tb\t2\n"), "OVERLAP_MISMATCH");
    // different overlaps within one graph
    const std::string nodes = "g\ta\tCCCC\t1\ng\tb\tCCCC\t1\ng\tc\tCCCC\t1\n";
    CHECK_EQ(build_code(nodes, "g\ta\tb\t2\ng\tb\tc\t1\n"), "INCONSISTENT_OVERLAP");
    CHECK_EQ(build_code(nodes, "g\ta\tb\t2\ng\tb\tc\t2\n"), "");
    // self loop allowed
    CHECK_EQ(build_code("g\ta\tCCCC\t1\n", "g\ta\ta\t2\n"), "");
}

// ---- search primitives -----------------------------------------------------
static void test_color_intersection() {
    using V = std::vector<uint32_t>;
    CHECK(intersect_colors(V{1, 2, 7}, V{2, 7, 9}) == V({2, 7}));
    CHECK(intersect_colors(V{1}, V{2}).empty());
    CHECK(intersect_colors(V{}, V{2}).empty());
    CHECK(intersect_colors(V{3, 4}, V{3, 4}) == V({3, 4}));
}

static void test_start_frame_rule() {
    CHECK(start_frame_allowed("CCATGCC", 2));   // ATG
    CHECK(start_frame_allowed("CCCCAT", 4));    // AT at last-but-one position
    CHECK(start_frame_allowed("CCCCCA", 5));    // A at last position
    CHECK(!start_frame_allowed("CCCCCC", 5));
    CHECK(!start_frame_allowed("CCCCTA", 4));   // TA is not a prefix of ATG
    CHECK(!start_frame_allowed("CCATCC", 2));   // ATC
    CHECK(!start_frame_allowed("CCAAGG", 2));
}

static void test_stop_codons() {
    CHECK(is_stop_codon("TAA"));
    CHECK(is_stop_codon("TAG"));
    CHECK(is_stop_codon("TGA"));
    CHECK(!is_stop_codon("ATG"));
    CHECK(!is_stop_codon("TTT"));
    CHECK(!is_stop_codon("TAC"));
}

// ---- traversal -------------------------------------------------------------
static void test_single_node_orf_and_candidate_record() {
    auto r = search("g\tn1\tCCATGCCCGCCTAACC\t1,2\n", "");
    CHECK_EQ(r.candidates.size(), 1u);
    const Candidate& c = r.candidates[0];
    CHECK_EQ(c.path, "n1");
    CHECK_EQ(c.start_offset, 2);
    CHECK_EQ(c.length_nt, 12);
    CHECK_EQ(c.sequence, "ATGCCCGCCTAA");
    CHECK(c.support == std::vector<uint32_t>({1, 2}));
    CHECK_EQ(r.stats.search_states, 1u);
    CHECK_EQ(r.stats.candidates, 1u);
    CHECK(r.stats.exhaustive());
}

static void test_each_stop_codon_terminates() {
    for (const char* stop : {"TAA", "TAG", "TGA"}) {
        auto r = search(std::string("g\tn\tATGCCC") + stop + "CC\t1\n", "");
        CHECK_EQ(r.candidates.size(), 1u);
        if (!r.candidates.empty()) CHECK_EQ(r.candidates[0].sequence, std::string("ATGCCC") + stop);
    }
}

static void test_first_inframe_stop_wins() {
    // out-of-frame TAA at 4-6 ignored; first in-frame stop is TAG at 9-11; n2 never entered
    auto r = search("g\tn1\tATGCTAACCTAGCCCTAACC\t1\ng\tn2\tGGG\t1\n", "g\tn1\tn2\t0\n");
    CHECK_EQ(r.candidates.size(), 1u);
    CHECK_EQ(r.candidates[0].sequence, "ATGCTAACCTAG");
    CHECK_EQ(r.stats.search_states, 1u);
}

static void test_frame_tracking_across_nodes_with_overlap() {
    // K=3: spelled = n1 + n2[3:] + n3[3:]
    auto r = search("g\tn1\tCCATGCCG\t1,2\ng\tn2\tCCGGCCGCC\t1,2\ng\tn3\tGCCTAACC\t1\n",
                    "g\tn1\tn2\t3\ng\tn2\tn3\t3\n");
    CHECK_EQ(r.candidates.size(), 1u);
    CHECK_EQ(r.candidates[0].path, "n1>n2>n3");
    CHECK_EQ(r.candidates[0].start_offset, 2);
    CHECK_EQ(r.candidates[0].length_nt, 15);
    CHECK_EQ(r.candidates[0].sequence, "ATGCCGGCCGCCTAA");
    CHECK(r.candidates[0].support == std::vector<uint32_t>({1}));
}

static void test_start_codon_spanning_nodes() {
    // AT|G across the boundary; via n3 the first codon is ATC (start_rejected)
    auto r = search("g\tn1\tCCCCAT\t1\ng\tn2\tGCCCTGACC\t1\ng\tn3\tCCTAACC\t1\n",
                    "g\tn1\tn2\t0\ng\tn1\tn3\t0\n");
    CHECK_EQ(r.candidates.size(), 1u);
    CHECK_EQ(r.candidates[0].path, "n1>n2");
    CHECK_EQ(r.candidates[0].start_offset, 4);
    CHECK_EQ(r.candidates[0].sequence, "ATGCCCTGA");
    CHECK_EQ(r.stats.start_rejected, 1u);
}

static void test_start_ownership_with_overlap() {
    // K=2: the last 2 bases of n1 (which has a successor) are owned by n2, so no start at n1@4.
    auto r = search("g\tn1\tCCCCAT\t1\ng\tn2\tATGCCCTAA\t1\n", "g\tn1\tn2\t2\n");
    CHECK_EQ(r.candidates.size(), 1u);
    CHECK_EQ(r.candidates[0].path, "n2");
    CHECK_EQ(r.candidates[0].start_offset, 0);
}

static void test_branching_dead_end() {
    auto r = search("g\tn1\tCCATGCCC\t1\ng\tn2\tGGGTAACC\t1\ng\tn3\tGGTAACCC\t1\n",
                    "g\tn1\tn2\t0\ng\tn1\tn3\t0\n");
    CHECK(paths(r) == std::vector<std::string>({"n1>n2"}));
    CHECK_EQ(r.stats.dead_ends, 1u);
}

static void test_strict_vs_permissive() {
    const std::string nodes = "g\tn1\tATGCCC\t1\ng\tn2\tGCCGCC\t1,2\ng\tn3\tGCCTAAC\t2\n"
                              "g\tn4\tGCCTGAC\t1\ng\tn5\tGCCTAAC\t.\n";
    const std::string edges = "g\tn1\tn2\t0\ng\tn2\tn3\t0\ng\tn2\tn4\t0\ng\tn2\tn5\t0\n";
    auto s = search(nodes, edges, Policy::Strict);
    CHECK(paths(s) == std::vector<std::string>({"n1>n2>n4"}));
    CHECK_EQ(s.stats.color_pruned, 2u);  // n3 (empty intersection) and n5 (no colours)
    auto p = search(nodes, edges, Policy::Permissive);
    CHECK_EQ(p.candidates.size(), 2u);
    CHECK_EQ(p.candidates[0].path, "n1>n2>n3");
    CHECK(p.candidates[0].support.empty());  // fragmented_support
    CHECK_EQ(p.stats.color_pruned, 1u);      // only n5
}

static void test_color_gate_on_start_node() {
    // Two start frames (ATG at 0, lone A at 5, spec 4.2 note 2); both stopped by the gate.
    auto s = search("g\tn\tATGTAA\t.\n", "", Policy::Strict);
    CHECK(s.candidates.empty());
    CHECK_EQ(s.stats.color_pruned, 2u);
    auto p = search("g\tn\tATGTAA\t.\n", "", Policy::Permissive);
    CHECK(p.candidates.empty());
    CHECK_EQ(p.stats.color_pruned, 2u);
}

static void test_cycle_termination_by_visit_bound() {
    auto r = search("g\tn1\tATGCCC\t1\ng\tn2\tGCCGCC\t1\ng\tn3\tCGGCCG\t1\n",
                    "g\tn1\tn2\t0\ng\tn2\tn3\t0\ng\tn3\tn2\t0\n");
    CHECK(r.candidates.empty());
    CHECK_EQ(r.stats.search_states, 5u);
    CHECK_EQ(r.stats.node_visit_cuts, 1u);
    CHECK_EQ(r.stats.max_depth, 5u);
    CHECK(!r.stats.exhaustive());
}

static void test_bounded_revisit_finds_shifted_frame() {
    const std::string nodes = "g\tn1\tATGCCC\t1\ng\tr\tGCC\t1\ng\tn3\tCTAACC\t1\ng\tx\tGG\t1\n";
    const std::string edges = "g\tn1\tr\t0\ng\tr\tn3\t0\ng\tr\tx\t0\ng\tx\tr\t0\n";
    auto r = search(nodes, edges);
    CHECK(paths(r) == std::vector<std::string>({"n1>r>x>r>n3"}));
    CHECK_EQ(r.candidates[0].length_nt, 18);
    CHECK_EQ(r.stats.search_states, 7u);
    CHECK_EQ(r.stats.dead_ends, 1u);
    CHECK_EQ(r.stats.node_visit_cuts, 1u);
    Limits lim;
    lim.max_node_visits = 1;
    auto r1 = search(nodes, edges, Policy::Strict, lim);
    CHECK(r1.candidates.empty());
}

static void test_orf_length_cut() {
    Limits lim;
    lim.max_orf_nt = 9;
    auto r = search("g\tn1\tCCATGCCCGCCTAACC\t1\n", "", Policy::Strict, lim);
    CHECK(r.candidates.empty());
    CHECK_EQ(r.stats.orf_length_cuts, 1u);
    lim.max_orf_nt = 12;  // stop check precedes the length cut
    auto r2 = search("g\tn1\tCCATGCCCGCCTAACC\t1\n", "", Policy::Strict, lim);
    CHECK_EQ(r2.candidates.size(), 1u);
    CHECK_EQ(r2.stats.orf_length_cuts, 0u);
}

static void test_path_length_cut() {
    Limits lim;
    lim.max_path_nodes = 2;
    auto r = search("g\tn1\tCCATGCCG\t1,2\ng\tn2\tCCGGCCGCC\t1,2\ng\tn3\tGCCTAACC\t1\n",
                    "g\tn1\tn2\t3\ng\tn2\tn3\t3\n", Policy::Strict, lim);
    CHECK(r.candidates.empty());
    CHECK_EQ(r.stats.path_length_cuts, 1u);
}

static void test_state_limit_abort() {
    Limits lim;
    lim.max_states = 2;
    auto r = search("g\tn1\tATGCCC\t1,2\ng\tn2\tGCCTAACC\t1\ng\tn3\tGGGCCCTGACC\t2\n",
                    "g\tn1\tn2\t0\ng\tn1\tn3\t0\n", Policy::Strict, lim);
    CHECK_EQ(r.candidates.size(), 1u);
    CHECK_EQ(r.candidates[0].path, "n1>n2");
    CHECK_EQ(r.stats.search_states, 2u);
    CHECK(r.stats.state_limit_hit);
    CHECK(!r.stats.exhaustive());
}

static void test_no_duplicates() {
    auto r = search("g\tn1\tATGCCC\t1\ng\tn2\tGCCTAACC\t1\ng\tn3\tGGGCCCTGACC\t1\n",
                    "g\tn1\tn2\t0\ng\tn1\tn3\t0\n");
    CHECK_EQ(r.dropped_duplicates, 0u);
}

// ---- runs and rendering ----------------------------------------------------
static void test_render_and_ordering() {
    // graphs given in reverse order; both policies; permissive sorts before strict (bytes)
    auto gs = build("z\tn\tATGCCCTAAC\t1\ny\tn\tATGCCCTAAC\t.\n", "");
    auto runs = run_all(gs, PolicyChoice::Both, Limits());
    CHECK_EQ(runs.size(), 4u);
    canonicalize(runs);
    const std::string cand = render_candidates(runs);
    const std::string expect_c =
        "graph_id\tpolicy\tcandidate_id\tpath\tstart_offset\tlength_nt\tsequence\t"
        "support_colors\tstatus\n"
        "z\tpermissive\t1\tn\t0\t9\tATGCCCTAA\t1\tshared_support\n"
        "z\tstrict\t1\tn\t0\t9\tATGCCCTAA\t1\tshared_support\n";
    CHECK_EQ(cand, expect_c);
    const std::string summ = render_summary(runs);
    const std::string expect_s =
        "graph_id\tpolicy\tsearch_states\tmax_depth\tcandidates\tstart_rejected\tcolor_pruned\t"
        "dead_ends\torf_length_cuts\tpath_length_cuts\tnode_visit_cuts\tstate_limit_hit\t"
        "exhaustive\n"
        "y\tpermissive\t1\t1\t0\t0\t1\t0\t0\t0\t0\t0\t1\n"
        "y\tstrict\t1\t1\t0\t0\t1\t0\t0\t0\t0\t0\t1\n"
        "z\tpermissive\t1\t1\t1\t0\t0\t0\t0\t0\t0\t0\t1\n"
        "z\tstrict\t1\t1\t1\t0\t0\t0\t0\t0\t0\t0\t1\n";
    CHECK_EQ(summ, expect_s);
}

static void test_render_fragmented_and_candidate_ids() {
    auto gs = build("g\tn1\tATGCCC\t1\ng\tn2\tGCCTAACC\t2\ng\tn3\tGCCTGACC\t1\n",
                    "g\tn1\tn2\t0\ng\tn1\tn3\t0\n");
    auto runs = run_all(gs, PolicyChoice::Permissive, Limits());
    canonicalize(runs);
    const std::string cand = render_candidates(runs);
    CHECK(cand.find("g\tpermissive\t1\tn1>n2\t0\t12\tATGCCCGCCTAA\t.\tfragmented_support\n") !=
          std::string::npos);
    CHECK(cand.find("g\tpermissive\t2\tn1>n3\t0\t12\tATGCCCGCCTGA\t1\tshared_support\n") !=
          std::string::npos);
}

static void test_empty_graph_set() {
    auto gs = build("", "");
    CHECK(gs.empty());
    auto runs = run_all(gs, PolicyChoice::Both, Limits());
    CHECK(runs.empty());
    CHECK_EQ(render_candidates(runs).find('\n'), render_candidates(runs).size() - 1);  // header only
}

// Spec v1.1: strict runs before permissive; run_all keeps emission order; canonicalize sorts.
static void test_pipeline_contract() {
    std::vector<Policy> both = policies_for(PolicyChoice::Both);
    CHECK(both.size() == 2 && both[0] == Policy::Strict && both[1] == Policy::Permissive);
    auto gs = build("G\ta\tATGCATGC\t1\nG\tb\tCCTAA\t1\nG\tc\tATAA\t1\n",
                    "G\ta\tb\t0\nG\ta\tc\t0\n");
    auto runs = run_all(gs, PolicyChoice::Both, Limits());
    CHECK_EQ(runs.size(), 2u);
    CHECK(runs[0].policy == Policy::Strict);  // execution order, not output order
    CHECK_EQ(runs[0].result.candidates.size(), 2u);
    CHECK_EQ(runs[0].result.candidates[0].path, std::string("a>c"));  // DFS emission order
    CHECK_EQ(runs[0].result.candidates[1].path, std::string("a>b"));
    canonicalize(runs);
    CHECK(runs[0].policy == Policy::Permissive);  // permissive < strict (bytes)
    CHECK_EQ(runs[0].result.candidates[0].path, std::string("a>b"));
    CHECK_EQ(runs[0].result.candidates[0].start_offset, 4);
    CHECK_EQ(runs[0].result.candidates[1].path, std::string("a>c"));
}

int main() {
    test_dna_validation();
    test_id_validation();
    test_color_parsing();
    test_int_parsing();
    test_table_and_headers();
    test_graph_construction();
    test_overlap_validation();
    test_overlap_mismatch_and_consistency();
    test_color_intersection();
    test_start_frame_rule();
    test_stop_codons();
    test_single_node_orf_and_candidate_record();
    test_each_stop_codon_terminates();
    test_first_inframe_stop_wins();
    test_frame_tracking_across_nodes_with_overlap();
    test_start_codon_spanning_nodes();
    test_start_ownership_with_overlap();
    test_branching_dead_end();
    test_strict_vs_permissive();
    test_color_gate_on_start_node();
    test_cycle_termination_by_visit_bound();
    test_bounded_revisit_finds_shifted_frame();
    test_orf_length_cut();
    test_path_length_cut();
    test_state_limit_abort();
    test_no_duplicates();
    test_render_and_ordering();
    test_render_fragmented_and_candidate_ids();
    test_empty_graph_set();
    test_pipeline_contract();
    std::cout << (g_checks - g_failures) << "/" << g_checks << " checks passed\n";
    return g_failures == 0 ? 0 : 1;
}
