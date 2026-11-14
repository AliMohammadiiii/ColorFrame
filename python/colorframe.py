"""ColorFrame reference implementation (Python 3, standard library only).

Enumerates forward-strand ORFs on a small directed sequence graph with sample colours.
Normative references: ALGORITHM_SPEC.md (search, counters) and INPUT_OUTPUT_SCHEMA.md
(formats, validation order, exit codes). Clarity over speed.
"""
import argparse
import re
import sys
import time
from collections import namedtuple

STOP_CODONS = frozenset(("TAA", "TAG", "TGA"))
START_CODON = "ATG"
MAX_COLOR = 2147483647
INT64_MIN, INT64_MAX = -(2 ** 63), 2 ** 63 - 1

ID_RE = re.compile(r"[A-Za-z0-9_.-]+")
DNA_RE = re.compile(r"[ACGT]+")
UINT_RE = re.compile(r"[0-9]+")
INT_RE = re.compile(r"-?[0-9]+")

NODES_HEADER = ["graph_id", "node_id", "sequence", "colors"]
EDGES_HEADER = ["graph_id", "source", "target", "overlap_nt"]
CANDIDATES_HEADER = ["graph_id", "policy", "candidate_id", "path", "start_offset", "length_nt",
                     "sequence", "support_colors", "status"]
SUMMARY_HEADER = ["graph_id", "policy", "search_states", "max_depth", "candidates",
                  "start_rejected", "color_pruned", "dead_ends", "orf_length_cuts",
                  "path_length_cuts", "node_visit_cuts", "state_limit_hit", "exhaustive"]

Limits = namedtuple("Limits", "max_orf_nt max_path_nodes max_node_visits max_states")
DEFAULT_LIMITS = Limits(1200, 12, 2, 50000)
LIMIT_MINIMUMS = Limits(6, 1, 1, 1)


class ValidationError(Exception):
    """Input validation failure: exit status 2, `ERROR <CODE>: message`."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class UsageError(Exception):
    """Command-line / I/O usage failure: exit status 64."""


# --------------------------------------------------------------------------- field rules

def is_valid_id(text):
    return ID_RE.fullmatch(text) is not None


def is_valid_dna(text):
    return DNA_RE.fullmatch(text) is not None


def parse_colors(field):
    """`.` -> empty set; else strictly ascending non-negative ints without leading zeros."""
    if field == ".":
        return frozenset()
    values = []
    for token in field.split(","):
        if not UINT_RE.fullmatch(token) or (len(token) > 1 and token[0] == "0"):
            raise ValueError("bad colour token %r" % token)
        value = int(token)
        if value > MAX_COLOR or (values and value <= values[-1]):
            raise ValueError("colour out of range or not strictly ascending: %r" % token)
        values.append(value)
    return frozenset(values)


def parse_overlap(field):
    """`-?[0-9]+` fitting a signed 64-bit integer."""
    if not INT_RE.fullmatch(field):
        raise ValueError("not an integer: %r" % field)
    value = int(field)
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError("overlap does not fit in 64 bits: %r" % field)
    return value


def intersect_colors(active, colors):
    return active & colors


def can_start_frame(sequence, offset):
    """Spec 4.2 note 2: bases available from `offset` (max 3) must be a prefix of ATG."""
    return START_CODON.startswith(sequence[offset:offset + 3])


def startable_end(length, has_successors, overlap):
    """Spec 2.3: exclusive end of the start positions owned by a node."""
    return length - overlap if has_successors else length


def is_stop_codon(codon):
    return codon in STOP_CODONS


# --------------------------------------------------------------------------- parsing

def read_tsv(text, header, filename):
    """Split a TSV into (line_number, fields) rows after checking the header line."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()                      # optional trailing newline
    if not lines or lines[0].split("\t") != header:
        raise ValidationError("MALFORMED_INPUT", "%s line 1: missing or wrong header" % filename)
    # A blank line becomes the one-field row [""], so it fails the field-count check later.
    return [(i + 2, line.split("\t")) for i, line in enumerate(lines[1:])]


# --------------------------------------------------------------------------- graph model

class Graph:
    """Nodes indexed in sorted-id order; successors are sorted index lists (spec section 4)."""

    def __init__(self, graph_id, ids, seqs, colors, successors, overlap):
        self.graph_id = graph_id
        self.ids = ids
        self.seqs = seqs
        self.colors = colors
        self.successors = successors
        self.overlap = overlap           # K, shared by all edges (0 if there are none)


def _fail(code, filename, line, message):
    raise ValidationError(code, "%s line %d: %s" % (filename, line, message))


def build_graphs(node_rows, edge_rows):
    """Validate in the schema order (section 2) and return Graphs sorted by graph_id."""
    nodes = {}                           # graph_id -> {node_id: (seq, colours)}
    for line, f in node_rows:
        if len(f) != 4:
            _fail("MALFORMED_INPUT", "nodes.tsv", line, "expected 4 fields, got %d" % len(f))
        gid, nid, seq, col = f
        if not is_valid_id(gid) or not is_valid_id(nid):
            _fail("INVALID_ID", "nodes.tsv", line, "invalid identifier %r" % (gid if not is_valid_id(gid) else nid))
        if not is_valid_dna(seq):
            _fail("INVALID_DNA", "nodes.tsv", line, "invalid sequence %r" % seq)
        try:
            colors = parse_colors(col)
        except ValueError:
            _fail("INVALID_COLORS", "nodes.tsv", line, "invalid colours %r" % col)
        if nid in nodes.get(gid, {}):
            _fail("DUPLICATE_NODE", "nodes.tsv", line, "duplicate node %r in graph %r" % (nid, gid))
        nodes.setdefault(gid, {})[nid] = (seq, colors)

    edges = {gid: {} for gid in nodes}   # graph_id -> {(src, dst): overlap}
    overlaps = {gid: [] for gid in nodes}
    for line, f in edge_rows:
        if len(f) != 4:
            _fail("MALFORMED_INPUT", "edges.tsv", line, "expected 4 fields, got %d" % len(f))
        gid, src, dst, ov_field = f
        for ident in f[:3]:
            if not is_valid_id(ident):
                _fail("INVALID_ID", "edges.tsv", line, "invalid identifier %r" % ident)
        try:
            ov = parse_overlap(ov_field)
        except ValueError:
            _fail("MALFORMED_INPUT", "edges.tsv", line, "overlap_nt is not an integer: %r" % ov_field)
        if gid not in nodes or src not in nodes[gid] or dst not in nodes[gid]:
            _fail("MISSING_NODE", "edges.tsv", line, "edge %s->%s references an unknown node or graph %r" % (src, dst, gid))
        if (src, dst) in edges[gid]:
            _fail("DUPLICATE_EDGE", "edges.tsv", line, "duplicate edge %s->%s in graph %r" % (src, dst, gid))
        s_seq, d_seq = nodes[gid][src][0], nodes[gid][dst][0]
        if ov < 0 or ov > len(s_seq) or ov >= len(d_seq):
            _fail("INVALID_OVERLAP", "edges.tsv", line, "overlap %d out of range for %s->%s" % (ov, src, dst))
        if ov and s_seq[-ov:] != d_seq[:ov]:
            _fail("OVERLAP_MISMATCH", "edges.tsv", line, "suffix of %s differs from prefix of %s for overlap %d" % (src, dst, ov))
        edges[gid][(src, dst)] = ov
        overlaps[gid].append((line, ov))

    graphs = []
    for gid in sorted(nodes):
        declared = overlaps[gid]
        if any(ov != declared[0][1] for _, ov in declared):
            line, ov = next((l, o) for l, o in declared if o != declared[0][1])
            _fail("INCONSISTENT_OVERLAP", "edges.tsv", line, "graph %r mixes overlaps %d and %d" % (gid, declared[0][1], ov))
        ids = sorted(nodes[gid])
        index = {nid: i for i, nid in enumerate(ids)}
        successors = [[] for _ in ids]
        for (src, dst) in edges[gid]:
            successors[index[src]].append(index[dst])
        for lst in successors:
            lst.sort()
        graphs.append(Graph(gid, ids, [nodes[gid][n][0] for n in ids], [nodes[gid][n][1] for n in ids],
                            successors, declared[0][1] if declared else 0))
    return graphs


# --------------------------------------------------------------------------- search

Candidate = namedtuple("Candidate", "path start_offset length_nt sequence support_colors status")


class Stats:
    """Per-search counters (spec 4.6)."""

    def __init__(self):
        self.search_states = 0
        self.max_depth = 0
        self.candidates = 0
        self.start_rejected = 0
        self.color_pruned = 0
        self.dead_ends = 0
        self.orf_length_cuts = 0
        self.path_length_cuts = 0
        self.node_visit_cuts = 0
        self.state_limit_hit = 0

    @property
    def exhaustive(self):
        cuts = self.orf_length_cuts + self.path_length_cuts + self.node_visit_cuts
        return 1 if cuts == 0 and not self.state_limit_hit else 0


SearchResult = namedtuple("SearchResult", "candidates stats duplicates_dropped")


class _Search:
    """One (graph, policy) search; ENTER mirrors the pseudocode of spec 4.2."""

    def __init__(self, graph, policy, limits):
        self.g = graph
        self.strict = policy == "strict"
        self.limits = limits
        self.stats = Stats()
        self.walk = []                                   # node indices of the current walk
        self.visits = [0] * len(graph.ids)
        self.seq = bytearray()                           # ORF bases so far
        self.active = frozenset()                        # colour intersection over the walk
        self.abort = False
        self.start_offset = 0
        self.candidates = []
        self.seen = set()                                # dedup keys (path, start_offset)
        self.duplicates_dropped = 0

    def run(self):
        g = self.g
        for u, seq in enumerate(g.seqs):
            for s in range(startable_end(len(seq), bool(g.successors[u]), g.overlap)):
                if not can_start_frame(seq, s):
                    continue                             # no frame created
                self.start_offset = s
                self.enter(u, s, True)
                if self.abort:
                    return

    def enter(self, v, offset, is_start):
        st, lim, g = self.stats, self.limits, self.g
        if st.search_states == lim.max_states:           # immediate abort on the state limit
            st.state_limit_hit = 1
            self.abort = True
            return
        st.search_states += 1
        self.walk.append(v)
        self.visits[v] += 1
        st.max_depth = max(st.max_depth, len(self.walk))
        saved_active = self.active
        mark = len(self.seq)
        self.active = g.colors[v] if is_start else intersect_colors(self.active, g.colors[v])

        # Colour gate, evaluated before any base of v is read.
        if (self.strict and not self.active) or (not self.strict and not g.colors[v]):
            st.color_pruned += 1
        elif self.read_bases(v, offset, is_start):
            self.expand(v)

        # LEAVE: undo this frame's effects.
        del self.seq[mark:]
        self.active = saved_active
        self.visits[v] -= 1
        self.walk.pop()

    def read_bases(self, v, offset, is_start):
        """Append the node's contribution; return True if the ORF is still open afterwards."""
        st, seq = self.stats, self.seq
        contribution = self.g.seqs[v][offset:] if is_start else self.g.seqs[v][self.g.overlap:]
        for base in contribution.encode("ascii"):
            seq.append(base)
            n = len(seq)
            if n % 3 == 0:
                codon = seq[-3:].decode("ascii")
                if n == 3:
                    if codon != START_CODON:
                        st.start_rejected += 1
                        return False
                elif is_stop_codon(codon):
                    self.emit()
                    return False
            if n >= self.limits.max_orf_nt:
                st.orf_length_cuts += 1
                return False
        return True

    def expand(self, v):
        st, lim = self.stats, self.limits
        successors = self.g.successors[v]
        if not successors:
            st.dead_ends += 1
            return
        for w in successors:                              # sorted by target id
            if len(self.walk) >= lim.max_path_nodes:
                st.path_length_cuts += 1
                continue
            if self.visits[w] >= lim.max_node_visits:
                st.node_visit_cuts += 1
                continue
            self.enter(w, 0, False)
            if self.abort:
                return

    def emit(self):
        path = ">".join(self.g.ids[i] for i in self.walk)
        key = (path, self.start_offset)
        if key in self.seen:
            self.duplicates_dropped += 1
            return
        self.seen.add(key)
        colors = ",".join(str(c) for c in sorted(self.active)) or "."
        status = "shared_support" if self.active else "fragmented_support"
        self.candidates.append(Candidate(path, self.start_offset, len(self.seq),
                                         self.seq.decode("ascii"), colors, status))
        self.stats.candidates += 1


def search(graph, policy, limits):
    # Recursion depth is bounded by min(max_path_nodes, max_states); leave headroom.
    needed = min(limits.max_path_nodes, limits.max_states) + 1000
    if sys.getrecursionlimit() < needed:
        sys.setrecursionlimit(needed)
    s = _Search(graph, policy, limits)
    s.run()
    return SearchResult(s.candidates, s.stats, s.duplicates_dropped)


# --------------------------------------------------------------------------- output

def format_outputs(results):
    """results: list of (graph_id, policy, SearchResult). Returns (candidates_text, summary_text)."""
    cand_lines = ["\t".join(CANDIDATES_HEADER)]
    sum_lines = ["\t".join(SUMMARY_HEADER)]
    for gid, policy, res in sorted(results, key=lambda r: (r[0], r[1])):   # spec 4.5
        for rank, c in enumerate(sorted(res.candidates, key=lambda c: (c.path, c.start_offset)), 1):
            cand_lines.append("\t".join([gid, policy, str(rank), c.path, str(c.start_offset),
                                         str(c.length_nt), c.sequence, c.support_colors, c.status]))
        t = res.stats
        sum_lines.append("\t".join([gid, policy] + [str(x) for x in (
            t.search_states, t.max_depth, t.candidates, t.start_rejected, t.color_pruned,
            t.dead_ends, t.orf_length_cuts, t.path_length_cuts, t.node_visit_cuts,
            t.state_limit_hit, t.exhaustive)]))
    return "\n".join(cand_lines) + "\n", "\n".join(sum_lines) + "\n"


# --------------------------------------------------------------------------- CLI

class _Parser(argparse.ArgumentParser):
    def error(self, message):                            # argparse would exit 2; we need 64
        raise UsageError(message)


def _limit(name, minimum):
    def convert(text):
        if not re.fullmatch(r"[0-9]+", text):
            raise argparse.ArgumentTypeError("%s must be an integer" % name)
        value = int(text)
        if value < minimum:
            raise argparse.ArgumentTypeError("%s must be >= %d" % (name, minimum))
        return value
    return convert


def parse_args(argv):
    p = _Parser(prog="colorframe", add_help=False, allow_abbrev=False)
    p.add_argument("--nodes", required=True)
    p.add_argument("--edges", required=True)
    p.add_argument("--policy", required=True, choices=["strict", "permissive", "both"])
    p.add_argument("--out", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--timings")
    for name, default, minimum in zip(Limits._fields, DEFAULT_LIMITS, LIMIT_MINIMUMS):
        flag = "--" + name.replace("_", "-")
        p.add_argument(flag, dest=name, default=default, type=_limit(flag, minimum))
    return p.parse_args(argv)


def _read(path):
    try:
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise UsageError("cannot read %s: %s" % (path, e))


def _write(path, text):
    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    except OSError as e:
        raise UsageError("cannot write %s: %s" % (path, e))


def run_pipeline(args):
    clock = time.perf_counter_ns
    t0 = clock()
    node_rows = read_tsv(_read(args.nodes), NODES_HEADER, "nodes.tsv")
    edge_rows = read_tsv(_read(args.edges), EDGES_HEADER, "edges.tsv")
    t1 = clock()
    graphs = build_graphs(node_rows, edge_rows)
    t2 = clock()
    limits = Limits(args.max_orf_nt, args.max_path_nodes, args.max_node_visits, args.max_states)
    policies = ["strict", "permissive"] if args.policy == "both" else [args.policy]
    results = [(g.graph_id, pol, search(g, pol, limits)) for g in graphs for pol in policies]
    t3 = clock()
    cand_text, sum_text = format_outputs(results)
    _write(args.out, cand_text)
    _write(args.summary, sum_text)
    t4 = clock()
    if args.timings:
        phases = [("parse", t1 - t0), ("validate", t2 - t1), ("search", t3 - t2),
                  ("write", t4 - t3), ("total", t4 - t0)]
        _write(args.timings, "phase\tms\n" + "".join("%s\t%.3f\n" % (n, d / 1e6) for n, d in phases))


def main(argv=None):
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        run_pipeline(args)
    except UsageError as e:
        sys.stderr.write("ERROR USAGE: %s\n" % e)
        return 64
    except ValidationError as e:
        sys.stderr.write("ERROR %s: %s\n" % (e.code, e.message))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
