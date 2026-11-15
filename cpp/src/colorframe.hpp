// ColorFrame: bounded ORF candidate search over a small coloured sequence graph.
// Spec: ALGORITHM_SPEC.md (search), INPUT_OUTPUT_SCHEMA.md (formats, errors).
#pragma once

#include <cstdint>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace cf {

// ---- Validation errors (INPUT_OUTPUT_SCHEMA.md section 2) ------------------
struct ValidationError : std::runtime_error {
    std::string code;  // e.g. "INVALID_DNA"
    ValidationError(std::string c, const std::string& msg)
        : std::runtime_error(msg), code(std::move(c)) {}
};

// ---- Field-level validation ------------------------------------------------
bool is_valid_id(const std::string& s);   // [A-Za-z0-9_.-]+
bool is_valid_dna(const std::string& s);  // non-empty, only A C G T
// "." -> empty set; else strictly ascending non-negative ints, no leading zeros, <= 2^31-1.
bool parse_colors(const std::string& s, std::vector<uint32_t>& out);
// "-?[0-9]+" fitting int64; false otherwise.
bool parse_int64(const std::string& s, int64_t& out);

// ---- Tables and graph construction ----------------------------------------
// A TSV file split into lines and tab-separated fields. rows[0] is the header.
struct Table {
    std::string name;
    std::vector<std::vector<std::string>> rows;
};
Table parse_table(const std::string& text, const std::string& name);

struct Node {
    std::string id;
    std::string seq;
    std::vector<uint32_t> colors;  // sorted ascending
};

// One graph with nodes sorted by id; successors are sorted node indices (= sorted by target id).
struct Graph {
    std::string id;
    std::vector<Node> nodes;
    std::vector<std::vector<int>> succ;
    int64_t overlap = 0;  // K, the uniform overlap of all edges (0 without edges)
};

// Validates everything in the schema's order and returns graphs sorted by graph_id.
// Throws ValidationError on the first defect.
std::vector<Graph> build_graphs(const Table& nodes, const Table& edges);

// ---- Search ----------------------------------------------------------------
enum class Policy { Strict, Permissive };
const char* policy_name(Policy p);

struct Limits {
    int64_t max_orf_nt = 1200;
    int64_t max_path_nodes = 12;
    int64_t max_node_visits = 2;
    int64_t max_states = 50000;
};

struct Candidate {
    std::string path;  // node ids joined by '>'
    int64_t start_offset = 0;
    int64_t length_nt = 0;
    std::string sequence;
    std::vector<uint32_t> support;  // empty -> fragmented_support
};

struct Stats {
    uint64_t search_states = 0, max_depth = 0, candidates = 0, start_rejected = 0,
             color_pruned = 0, dead_ends = 0, orf_length_cuts = 0, path_length_cuts = 0,
             node_visit_cuts = 0;
    bool state_limit_hit = false;
    bool exhaustive() const {
        return orf_length_cuts == 0 && path_length_cuts == 0 && node_visit_cuts == 0 &&
               !state_limit_hit;
    }
};

struct SearchResult {
    std::vector<Candidate> candidates;  // in discovery order (unsorted)
    Stats stats;
    uint64_t dropped_duplicates = 0;  // must stay 0 (spec 4.4)
};

// Helpers exposed for unit tests.
std::vector<uint32_t> intersect_colors(const std::vector<uint32_t>& a,
                                       const std::vector<uint32_t>& b);
bool is_stop_codon(const char* three);  // TAA, TAG, TGA
// Spec 4.2: may a start frame be created at offset s of `seq`? (bases from s prefix of "ATG")
bool start_frame_allowed(const std::string& seq, size_t s);

SearchResult search_graph(const Graph& g, Policy policy, const Limits& limits);

// ---- Runs and output -------------------------------------------------------
enum class PolicyChoice { Strict, Permissive, Both };

struct Run {
    std::string graph_id;
    Policy policy;
    SearchResult result;
};

// Policies in execution order: strict before permissive (spec v1.1).
std::vector<Policy> policies_for(PolicyChoice choice);
// Search phase: every graph in id order, policies in execution order; candidates stay in
// discovery order and runs in execution order (no sorting here).
std::vector<Run> run_all(const std::vector<Graph>& graphs, PolicyChoice choice,
                         const Limits& limits);
// Canonicalize phase (spec 4.5): runs by (graph, policy name), candidates by (path, start).
void canonicalize(std::vector<Run>& runs);
std::string render_candidates(const std::vector<Run>& runs);
std::string render_summary(const std::vector<Run>& runs);

}  // namespace cf
