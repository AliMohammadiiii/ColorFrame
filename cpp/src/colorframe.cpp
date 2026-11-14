#include "colorframe.hpp"

#include <algorithm>
#include <iterator>
#include <map>
#include <tuple>

namespace cf {

// ============================================================================
// Field-level validation
// ============================================================================

bool is_valid_id(const std::string& s) {
    if (s.empty()) return false;
    for (char c : s) {
        bool ok = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
                  c == '_' || c == '.' || c == '-';
        if (!ok) return false;
    }
    return true;
}

bool is_valid_dna(const std::string& s) {
    if (s.empty()) return false;
    for (char c : s)
        if (c != 'A' && c != 'C' && c != 'G' && c != 'T') return false;
    return true;
}

bool parse_colors(const std::string& s, std::vector<uint32_t>& out) {
    out.clear();
    if (s == ".") return true;
    if (s.empty()) return false;
    size_t i = 0;
    while (i <= s.size()) {
        size_t j = s.find(',', i);
        if (j == std::string::npos) j = s.size();
        std::string tok = s.substr(i, j - i);
        if (tok.empty() || tok.size() > 10) return false;
        if (tok.size() > 1 && tok[0] == '0') return false;  // no leading zeros
        uint64_t v = 0;
        for (char c : tok) {
            if (c < '0' || c > '9') return false;
            v = v * 10 + static_cast<uint64_t>(c - '0');
        }
        if (v > 2147483647ull) return false;
        if (!out.empty() && v <= out.back()) return false;  // strictly ascending
        out.push_back(static_cast<uint32_t>(v));
        if (j == s.size()) break;
        i = j + 1;
    }
    return true;
}

bool parse_int64(const std::string& s, int64_t& out) {
    size_t i = 0;
    bool neg = false;
    if (i < s.size() && s[i] == '-') { neg = true; ++i; }
    if (i >= s.size()) return false;
    // Accumulate as a negative number so INT64_MIN is representable.
    int64_t v = 0;
    const int64_t lo = INT64_MIN;
    for (; i < s.size(); ++i) {
        if (s[i] < '0' || s[i] > '9') return false;
        int d = s[i] - '0';
        if (v < (lo + d) / 10) return false;  // v*10 - d would underflow
        v = v * 10 - d;
    }
    if (!neg) {
        if (v == lo) return false;
        v = -v;
    }
    out = v;
    return true;
}

// ============================================================================
// Tables and graph construction
// ============================================================================

Table parse_table(const std::string& text, const std::string& name) {
    Table t;
    t.name = name;
    size_t pos = 0;
    while (pos < text.size()) {
        size_t nl = text.find('\n', pos);
        if (nl == std::string::npos) nl = text.size();
        std::vector<std::string> fields;
        size_t f = pos;
        while (true) {
            size_t tab = text.find('\t', f);
            if (tab == std::string::npos || tab >= nl) {
                fields.push_back(text.substr(f, nl - f));
                break;
            }
            fields.push_back(text.substr(f, tab - f));
            f = tab + 1;
        }
        t.rows.push_back(std::move(fields));
        pos = nl + 1;
    }
    return t;
}

namespace {

[[noreturn]] void fail(const std::string& code, const Table& t, size_t row, const std::string& what) {
    throw ValidationError(code, t.name + " line " + std::to_string(row + 1) + ": " + what);
}

void check_header(const Table& t, const std::vector<std::string>& expected) {
    if (t.rows.empty()) throw ValidationError("MALFORMED_INPUT", t.name + ": missing header");
    if (t.rows[0] != expected)
        throw ValidationError("MALFORMED_INPUT", t.name + " line 1: unexpected header");
}

struct EdgeRec {
    std::string src, tgt;
    int64_t overlap;
};

struct GraphBuild {
    std::map<std::string, Node> nodes;  // sorted by id
    std::vector<EdgeRec> edges;         // file order
    std::set<std::pair<std::string, std::string>> edge_set;
};

}  // namespace

std::vector<Graph> build_graphs(const Table& nodes, const Table& edges) {
    std::map<std::string, GraphBuild> gb;  // sorted by graph_id

    // Step 1: nodes.
    check_header(nodes, {"graph_id", "node_id", "sequence", "colors"});
    for (size_t r = 1; r < nodes.rows.size(); ++r) {
        const auto& row = nodes.rows[r];
        if (row.size() != 4) fail("MALFORMED_INPUT", nodes, r, "expected 4 fields");
        if (!is_valid_id(row[0])) fail("INVALID_ID", nodes, r, "graph_id '" + row[0] + "'");
        if (!is_valid_id(row[1])) fail("INVALID_ID", nodes, r, "node_id '" + row[1] + "'");
        if (!is_valid_dna(row[2])) fail("INVALID_DNA", nodes, r, "sequence '" + row[2] + "'");
        Node n;
        n.id = row[1];
        n.seq = row[2];
        if (!parse_colors(row[3], n.colors)) fail("INVALID_COLORS", nodes, r, "colors '" + row[3] + "'");
        auto& g = gb[row[0]];
        if (g.nodes.count(n.id)) fail("DUPLICATE_NODE", nodes, r, "node '" + n.id + "' repeated");
        g.nodes.emplace(n.id, std::move(n));
    }

    // Step 2: edges.
    check_header(edges, {"graph_id", "source", "target", "overlap_nt"});
    for (size_t r = 1; r < edges.rows.size(); ++r) {
        const auto& row = edges.rows[r];
        if (row.size() != 4) fail("MALFORMED_INPUT", edges, r, "expected 4 fields");
        for (int i = 0; i < 3; ++i)
            if (!is_valid_id(row[i])) fail("INVALID_ID", edges, r, "identifier '" + row[i] + "'");
        int64_t ov;
        if (!parse_int64(row[3], ov)) fail("MALFORMED_INPUT", edges, r, "overlap_nt '" + row[3] + "'");
        auto git = gb.find(row[0]);
        if (git == gb.end()) fail("MISSING_NODE", edges, r, "graph '" + row[0] + "' not in nodes file");
        GraphBuild& g = git->second;
        auto s = g.nodes.find(row[1]);
        auto t = g.nodes.find(row[2]);
        if (s == g.nodes.end()) fail("MISSING_NODE", edges, r, "source '" + row[1] + "'");
        if (t == g.nodes.end()) fail("MISSING_NODE", edges, r, "target '" + row[2] + "'");
        if (!g.edge_set.insert({row[1], row[2]}).second)
            fail("DUPLICATE_EDGE", edges, r, row[1] + " -> " + row[2] + " repeated");
        const std::string& a = s->second.seq;
        const std::string& b = t->second.seq;
        if (ov < 0 || ov > static_cast<int64_t>(a.size()) || ov >= static_cast<int64_t>(b.size()))
            fail("INVALID_OVERLAP", edges, r, "overlap_nt " + row[3] + " out of range");
        size_t k = static_cast<size_t>(ov);
        if (a.compare(a.size() - k, k, b, 0, k) != 0)
            fail("OVERLAP_MISMATCH", edges, r, "suffix of source differs from prefix of target");
        g.edges.push_back({row[1], row[2], ov});
    }

    // Step 3: uniform overlap per graph, then build index-based graphs.
    std::vector<Graph> out;
    for (auto& kv : gb) {
        GraphBuild& b = kv.second;
        Graph g;
        g.id = kv.first;
        for (const auto& e : b.edges) {
            if (e.overlap != b.edges[0].overlap)
                throw ValidationError("INCONSISTENT_OVERLAP",
                                      "graph '" + g.id + "' declares different overlaps");
        }
        if (!b.edges.empty()) g.overlap = b.edges[0].overlap;
        std::map<std::string, int> index;
        for (auto& n : b.nodes) {
            index[n.first] = static_cast<int>(g.nodes.size());
            g.nodes.push_back(std::move(n.second));
        }
        g.succ.assign(g.nodes.size(), {});
        for (const auto& e : b.edges) g.succ[index[e.src]].push_back(index[e.tgt]);
        for (auto& s : g.succ) std::sort(s.begin(), s.end());  // index order == id order
        out.push_back(std::move(g));
    }
    return out;
}

// ============================================================================
// Search (ALGORITHM_SPEC.md section 4)
// ============================================================================

const char* policy_name(Policy p) { return p == Policy::Strict ? "strict" : "permissive"; }

std::vector<uint32_t> intersect_colors(const std::vector<uint32_t>& a,
                                       const std::vector<uint32_t>& b) {
    std::vector<uint32_t> out;
    std::set_intersection(a.begin(), a.end(), b.begin(), b.end(), std::back_inserter(out));
    return out;
}

bool is_stop_codon(const char* c) {
    return c[0] == 'T' && ((c[1] == 'A' && (c[2] == 'A' || c[2] == 'G')) || (c[1] == 'G' && c[2] == 'A'));
}

bool start_frame_allowed(const std::string& seq, size_t s) {
    static const char kAtg[] = "ATG";
    size_t n = std::min<size_t>(3, seq.size() - s);
    return seq.compare(s, n, kAtg, n) == 0;
}

namespace {

class Searcher {
public:
    Searcher(const Graph& g, Policy p, const Limits& l)
        : g_(g), policy_(p), lim_(l), visits_(g.nodes.size(), 0) {}

    SearchResult run() {
        const int64_t K = g_.overlap;
        for (size_t u = 0; u < g_.nodes.size(); ++u) {
            const std::string& s = g_.nodes[u].seq;
            // Start-position ownership (spec 2.3).
            size_t limit = g_.succ[u].empty() ? s.size() : s.size() - static_cast<size_t>(K);
            for (size_t off = 0; off < limit; ++off) {
                if (!start_frame_allowed(s, off)) continue;
                start_offset_ = off;  // reported by EMIT for every walk from this frame
                enter(static_cast<int>(u), off, true);
                if (abort_) return std::move(res_);
            }
        }
        return std::move(res_);
    }

private:
    // ENTER from the pseudocode: count the state, push, expand, then LEAVE.
    void enter(int v, size_t start_offset, bool is_start) {
        Stats& st = res_.stats;
        if (st.search_states == static_cast<uint64_t>(lim_.max_states)) {
            st.state_limit_hit = true;
            abort_ = true;
            return;
        }
        ++st.search_states;
        walk_.push_back(v);
        ++visits_[v];
        st.max_depth = std::max<uint64_t>(st.max_depth, walk_.size());

        // Colour intersection lives in a per-depth buffer, so "restore on leave" is implicit.
        size_t d = walk_.size() - 1;
        if (active_.size() <= d) active_.resize(d + 1);
        const std::vector<uint32_t>& col = g_.nodes[v].colors;
        if (is_start) {
            active_[d] = col;
        } else {
            active_[d].clear();
            std::set_intersection(active_[d - 1].begin(), active_[d - 1].end(), col.begin(),
                                  col.end(), std::back_inserter(active_[d]));
        }

        const size_t seq_mark = seq_.size();
        expand(v, start_offset, is_start);

        seq_.resize(seq_mark);  // LEAVE: drop the bases this frame appended
        --visits_[v];
        walk_.pop_back();
    }

    void expand(int v, size_t start_offset, bool is_start) {
        Stats& st = res_.stats;
        const Node& node = g_.nodes[v];
        const std::vector<uint32_t>& active = active_[walk_.size() - 1];

        // Colour gate, before any base of v is read.
        if ((policy_ == Policy::Strict && active.empty()) ||
            (policy_ == Policy::Permissive && node.colors.empty())) {
            ++st.color_pruned;
            return;
        }

        size_t from = is_start ? start_offset : static_cast<size_t>(g_.overlap);
        for (size_t i = from; i < node.seq.size(); ++i) {
            seq_.push_back(node.seq[i]);
            const size_t len = seq_.size();
            if (len % 3 == 0) {
                const char* codon = seq_.data() + len - 3;
                if (len == 3) {
                    if (seq_ != "ATG") { ++st.start_rejected; return; }
                } else if (is_stop_codon(codon)) {
                    emit();
                    return;
                }
            }
            if (static_cast<int64_t>(len) >= lim_.max_orf_nt) {
                ++st.orf_length_cuts;
                return;
            }
        }

        // v exhausted, ORF still open.
        const std::vector<int>& next = g_.succ[v];
        if (next.empty()) { ++st.dead_ends; return; }
        for (int w : next) {
            if (static_cast<int64_t>(walk_.size()) >= lim_.max_path_nodes) { ++st.path_length_cuts; continue; }
            if (visits_[w] >= lim_.max_node_visits) { ++st.node_visit_cuts; continue; }
            enter(w, 0, false);
            if (abort_) return;
        }
    }

    // EMIT (spec 4.3) with the (path, start_offset) dedup set (spec 4.4).
    void emit() {
        Candidate c;
        for (size_t i = 0; i < walk_.size(); ++i) {
            if (i) c.path += '>';
            c.path += g_.nodes[walk_[i]].id;
        }
        c.start_offset = static_cast<int64_t>(start_offset_);
        c.length_nt = static_cast<int64_t>(seq_.size());
        c.sequence = seq_;
        c.support = active_[walk_.size() - 1];
        if (!seen_.insert({c.path, c.start_offset}).second) {
            ++res_.dropped_duplicates;
            return;
        }
        ++res_.stats.candidates;
        res_.candidates.push_back(std::move(c));
    }

private:
    const Graph& g_;
    Policy policy_;
    Limits lim_;
    SearchResult res_;
    std::vector<int> walk_;
    std::vector<int> visits_;
    std::string seq_;
    std::vector<std::vector<uint32_t>> active_;
    std::set<std::pair<std::string, int64_t>> seen_;
    bool abort_ = false;
    size_t start_offset_ = 0;  // offset of the current start frame within its node
};

}  // namespace

SearchResult search_graph(const Graph& g, Policy policy, const Limits& limits) {
    Searcher s(g, policy, limits);
    return s.run();
}

// ============================================================================
// Runs and output
// ============================================================================

std::vector<Run> run_all(const std::vector<Graph>& graphs, PolicyChoice choice,
                         const Limits& limits) {
    std::vector<Policy> policies;
    if (choice != PolicyChoice::Permissive) policies.push_back(Policy::Strict);
    if (choice != PolicyChoice::Strict) policies.push_back(Policy::Permissive);
    std::vector<Run> runs;
    for (const Graph& g : graphs) {
        for (Policy p : policies) {
            Run r{g.id, p, search_graph(g, p, limits)};
            // Canonical order within the group (spec 4.5).
            std::sort(r.result.candidates.begin(), r.result.candidates.end(),
                      [](const Candidate& a, const Candidate& b) {
                          int c = a.path.compare(b.path);
                          return c != 0 ? c < 0 : a.start_offset < b.start_offset;
                      });
            runs.push_back(std::move(r));
        }
    }
    std::sort(runs.begin(), runs.end(), [](const Run& a, const Run& b) {
        int c = a.graph_id.compare(b.graph_id);
        if (c != 0) return c < 0;
        return std::string(policy_name(a.policy)) < policy_name(b.policy);
    });
    return runs;
}

std::string render_candidates(const std::vector<Run>& runs) {
    std::string out =
        "graph_id\tpolicy\tcandidate_id\tpath\tstart_offset\tlength_nt\tsequence\t"
        "support_colors\tstatus\n";
    for (const Run& r : runs) {
        size_t id = 0;
        for (const Candidate& c : r.result.candidates) {
            std::string colors;
            for (uint32_t v : c.support) {
                if (!colors.empty()) colors += ',';
                colors += std::to_string(v);
            }
            if (colors.empty()) colors = ".";
            out += r.graph_id + '\t' + policy_name(r.policy) + '\t' + std::to_string(++id) + '\t' +
                   c.path + '\t' + std::to_string(c.start_offset) + '\t' +
                   std::to_string(c.length_nt) + '\t' + c.sequence + '\t' + colors + '\t' +
                   (c.support.empty() ? "fragmented_support" : "shared_support") + '\n';
        }
    }
    return out;
}

std::string render_summary(const std::vector<Run>& runs) {
    std::string out =
        "graph_id\tpolicy\tsearch_states\tmax_depth\tcandidates\tstart_rejected\tcolor_pruned\t"
        "dead_ends\torf_length_cuts\tpath_length_cuts\tnode_visit_cuts\tstate_limit_hit\t"
        "exhaustive\n";
    for (const Run& r : runs) {
        const Stats& s = r.result.stats;
        out += r.graph_id + '\t' + policy_name(r.policy);
        for (uint64_t v : {s.search_states, s.max_depth, s.candidates, s.start_rejected,
                           s.color_pruned, s.dead_ends, s.orf_length_cuts, s.path_length_cuts,
                           s.node_visit_cuts, uint64_t(s.state_limit_hit), uint64_t(s.exhaustive())})
            out += '\t' + std::to_string(v);
        out += '\n';
    }
    return out;
}

}  // namespace cf
