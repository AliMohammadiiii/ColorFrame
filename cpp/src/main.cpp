// ColorFrame CLI (INPUT_OUTPUT_SCHEMA.md section 3). Stages: parse, validate, search, canonicalize, write.
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>

#include "colorframe.hpp"

namespace {

using Clock = std::chrono::steady_clock;

struct UsageError {
    std::string msg;
};

double ms_since(Clock::time_point a, Clock::time_point b) {
    return std::chrono::duration<double, std::milli>(b - a).count();
}

std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw UsageError{"cannot read '" + path + "'"};
    std::ostringstream ss;
    ss << in.rdbuf();
    if (in.bad()) throw UsageError{"cannot read '" + path + "'"};
    return ss.str();
}

void write_file(const std::string& path, const std::string& data) {
    std::ofstream out(path, std::ios::binary);
    if (!out) throw UsageError{"cannot write '" + path + "'"};
    out << data;
    out.flush();
    if (!out) throw UsageError{"cannot write '" + path + "'"};
}

int64_t limit_value(const std::string& flag, const std::string& v, int64_t min) {
    int64_t x;
    bool digits = !v.empty() && v.find_first_not_of("0123456789") == std::string::npos;
    if (!digits || !cf::parse_int64(v, x)) throw UsageError{flag + " needs an integer, got '" + v + "'"};
    if (x < min) throw UsageError{flag + " must be >= " + std::to_string(min)};
    return x;
}

struct Options {
    std::string nodes, edges, out, summary, timings, policy;
    cf::Limits limits;
};

Options parse_args(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        std::string flag = argv[i];
        bool known = flag == "--nodes" || flag == "--edges" || flag == "--policy" ||
                     flag == "--out" || flag == "--summary" || flag == "--timings" ||
                     flag == "--max-orf-nt" || flag == "--max-path-nodes" ||
                     flag == "--max-node-visits" || flag == "--max-states";
        if (!known) throw UsageError{"unknown argument '" + flag + "'"};
        if (i + 1 >= argc) throw UsageError{flag + " needs a value"};
        std::string v = argv[++i];
        if (flag == "--nodes") o.nodes = v;
        else if (flag == "--edges") o.edges = v;
        else if (flag == "--policy") o.policy = v;
        else if (flag == "--out") o.out = v;
        else if (flag == "--summary") o.summary = v;
        else if (flag == "--timings") o.timings = v;
        else if (flag == "--max-orf-nt") o.limits.max_orf_nt = limit_value(flag, v, 6);
        else if (flag == "--max-path-nodes") o.limits.max_path_nodes = limit_value(flag, v, 1);
        else if (flag == "--max-node-visits") o.limits.max_node_visits = limit_value(flag, v, 1);
        else o.limits.max_states = limit_value(flag, v, 1);
    }
    const std::pair<const char*, const std::string*> required[] = {
        {"--nodes", &o.nodes}, {"--edges", &o.edges}, {"--policy", &o.policy},
        {"--out", &o.out}, {"--summary", &o.summary}};
    for (const auto& req : required)
        if (req.second->empty()) throw UsageError{std::string("missing required flag ") + req.first};
    if (o.policy != "strict" && o.policy != "permissive" && o.policy != "both")
        throw UsageError{"--policy must be strict, permissive or both"};
    return o;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        Options o = parse_args(argc, argv);
        auto t0 = Clock::now();
        std::string nodes_text = read_file(o.nodes);
        std::string edges_text = read_file(o.edges);
        cf::Table nodes = cf::parse_table(nodes_text, o.nodes);
        cf::Table edges = cf::parse_table(edges_text, o.edges);
        auto t1 = Clock::now();
        std::vector<cf::Graph> graphs;
        try {
            graphs = cf::build_graphs(nodes, edges);
        } catch (const cf::ValidationError& e) {
            std::fprintf(stderr, "ERROR %s: %s\n", e.code.c_str(), e.what());
            return 2;
        }
        auto t2 = Clock::now();
        cf::PolicyChoice choice = o.policy == "strict"       ? cf::PolicyChoice::Strict
                                  : o.policy == "permissive" ? cf::PolicyChoice::Permissive
                                                             : cf::PolicyChoice::Both;
        std::vector<cf::Run> runs = cf::run_all(graphs, choice, o.limits);
        auto t3 = Clock::now();
        cf::canonicalize(runs);
        auto t4 = Clock::now();
        write_file(o.out, cf::render_candidates(runs));
        write_file(o.summary, cf::render_summary(runs));
        auto t5 = Clock::now();
        if (!o.timings.empty()) {  // contiguous phases: total == sum (schema section 4)
            char buf[320];
            std::snprintf(buf, sizeof buf,
                          "phase\tms\nparse\t%.3f\nvalidate\t%.3f\nsearch\t%.3f\n"
                          "canonicalize\t%.3f\nwrite\t%.3f\ntotal\t%.3f\n",
                          ms_since(t0, t1), ms_since(t1, t2), ms_since(t2, t3), ms_since(t3, t4),
                          ms_since(t4, t5), ms_since(t0, t5));
            write_file(o.timings, buf);
        }
        return 0;
    } catch (const UsageError& e) {
        std::fprintf(stderr, "ERROR USAGE: %s\n", e.msg.c_str());
        return 64;
    }
}
