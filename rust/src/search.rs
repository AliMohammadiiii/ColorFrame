//! Bounded depth-first ORF search (ALGORITHM_SPEC.md section 4).
use std::collections::HashSet;

use crate::graph::Graph;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Policy {
    Strict,
    Permissive,
}

impl Policy {
    pub fn name(self) -> &'static str {
        match self {
            Policy::Strict => "strict",
            Policy::Permissive => "permissive",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Limits {
    pub max_orf_nt: usize,
    pub max_path_nodes: usize,
    pub max_node_visits: usize,
    pub max_states: usize,
}

impl Default for Limits {
    fn default() -> Self {
        Limits {
            max_orf_nt: 1200,
            max_path_nodes: 12,
            max_node_visits: 2,
            max_states: 50000,
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Stats {
    pub search_states: u64,
    pub max_depth: u64,
    pub candidates: u64,
    pub start_rejected: u64,
    pub color_pruned: u64,
    pub dead_ends: u64,
    pub orf_length_cuts: u64,
    pub path_length_cuts: u64,
    pub node_visit_cuts: u64,
    pub state_limit_hit: bool,
}

impl Stats {
    /// Section 4.6: no bound cut the search.
    pub fn exhaustive(&self) -> bool {
        self.orf_length_cuts == 0
            && self.path_length_cuts == 0
            && self.node_visit_cuts == 0
            && !self.state_limit_hit
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Candidate {
    pub path: String,
    pub start_offset: usize,
    pub length_nt: usize,
    pub sequence: String,
    pub colors: Vec<u32>,
    pub shared: bool,
}

#[derive(Debug, Clone)]
pub struct SearchResult {
    /// Sorted by (path, start_offset).
    pub candidates: Vec<Candidate>,
    pub stats: Stats,
    /// Duplicate (path, start_offset) records dropped; must be 0 (section 4.4).
    pub dup_dropped: usize,
}

/// `local` (bases available from the start offset, up to 3) must be a prefix of "ATG" (section 4.2 note 2).
pub fn start_frame_allowed(local: &[u8]) -> bool {
    b"ATG".starts_with(local)
}

pub fn is_stop_codon(codon: &[u8]) -> bool {
    matches!(codon, b"TAA" | b"TAG" | b"TGA")
}

/// Intersection of two sorted slices into `out` (cleared first).
pub fn intersect_sorted(a: &[u32], b: &[u32], out: &mut Vec<u32>) {
    out.clear();
    let (mut i, mut j) = (0, 0);
    while i < a.len() && j < b.len() {
        match a[i].cmp(&b[j]) {
            std::cmp::Ordering::Less => i += 1,
            std::cmp::Ordering::Greater => j += 1,
            std::cmp::Ordering::Equal => {
                out.push(a[i]);
                i += 1;
                j += 1;
            }
        }
    }
}

/// Search one graph under one policy (section 4.2).
pub fn search(graph: &Graph, policy: Policy, limits: &Limits) -> SearchResult {
    let mut s = Searcher {
        graph,
        policy,
        limits: *limits,
        stats: Stats::default(),
        walk: Vec::new(),
        visits: vec![0; graph.nodes.len()],
        seq: Vec::new(),
        active: Vec::new(),
        abort: false,
        start_offset: 0,
        candidates: Vec::new(),
        seen: HashSet::new(),
        dup_dropped: 0,
    };
    s.run();
    // Canonical order (section 4.5): path bytes, then start offset.
    s.candidates.sort_by(|a, b| {
        a.path
            .cmp(&b.path)
            .then(a.start_offset.cmp(&b.start_offset))
    });
    SearchResult {
        candidates: s.candidates,
        stats: s.stats,
        dup_dropped: s.dup_dropped,
    }
}

/// All mutable traversal state of one (graph, policy) search.
struct Searcher<'g> {
    graph: &'g Graph,
    policy: Policy,
    limits: Limits,
    stats: Stats,
    /// Current walk as node indices.
    walk: Vec<u32>,
    /// Occurrences of each node in the walk.
    visits: Vec<u32>,
    /// Bases spelled since the start position; truncated on backtrack.
    seq: Vec<u8>,
    /// `active[d]` = colour intersection of the walk prefix of length d+1 (reused buffers).
    active: Vec<Vec<u32>>,
    abort: bool,
    /// Start offset of the current start frame.
    start_offset: usize,
    candidates: Vec<Candidate>,
    seen: HashSet<(String, usize)>,
    dup_dropped: usize,
}

impl Searcher<'_> {
    fn run(&mut self) {
        let graph = self.graph;
        for (u, node) in graph.nodes.iter().enumerate() {
            for s in 0..graph.startable_end(u) {
                let local = &node.seq[s..(s + 3).min(node.seq.len())];
                if !start_frame_allowed(local) {
                    continue; // no frame created
                }
                self.start_offset = s;
                self.enter(u as u32, s, true);
                if self.abort {
                    return;
                }
            }
        }
    }

    /// ENTER + LEAVE of the pseudocode: `explore` returns early where the pseudocode
    /// says `goto LEAVE`, then the frame's state is undone here.
    fn enter(&mut self, v: u32, start_offset: usize, is_start: bool) {
        if self.stats.search_states == self.limits.max_states as u64 {
            self.stats.state_limit_hit = true;
            self.abort = true;
            return;
        }
        self.stats.search_states += 1;
        let depth = self.walk.len();
        self.walk.push(v);
        self.visits[v as usize] += 1;
        self.stats.max_depth = self.stats.max_depth.max(self.walk.len() as u64);
        if self.active.len() <= depth {
            self.active.push(Vec::new());
        }
        let seq_mark = self.seq.len();

        self.explore(v, start_offset, is_start, depth);

        self.seq.truncate(seq_mark);
        self.visits[v as usize] -= 1;
        self.walk.pop();
    }

    fn explore(&mut self, v: u32, start_offset: usize, is_start: bool, depth: usize) {
        let graph = self.graph;
        let node = &graph.nodes[v as usize];

        // Active colours: own colours at a start frame, else the parent's intersected.
        if is_start {
            let cur = &mut self.active[depth];
            cur.clear();
            cur.extend_from_slice(&node.colors);
        } else {
            let (prev, cur) = self.active.split_at_mut(depth);
            intersect_sorted(&prev[depth - 1], &node.colors, &mut cur[0]);
        }

        // Colour gate, evaluated before any base of v is read.
        let blocked = match self.policy {
            Policy::Strict => self.active[depth].is_empty(),
            Policy::Permissive => node.colors.is_empty(),
        };
        if blocked {
            self.stats.color_pruned += 1;
            return;
        }

        let from = if is_start {
            start_offset
        } else {
            graph.overlap
        };
        for &b in &node.seq[from..] {
            self.seq.push(b);
            let len = self.seq.len();
            if len.is_multiple_of(3) {
                let codon = &self.seq[len - 3..];
                if len == 3 {
                    if codon != b"ATG" {
                        self.stats.start_rejected += 1;
                        return;
                    }
                } else if is_stop_codon(codon) {
                    self.emit(depth);
                    return;
                }
            }
            if len >= self.limits.max_orf_nt {
                self.stats.orf_length_cuts += 1;
                return;
            }
        }

        // v exhausted, ORF still open.
        if node.succ.is_empty() {
            self.stats.dead_ends += 1;
            return;
        }
        for &w in &node.succ {
            if self.walk.len() >= self.limits.max_path_nodes {
                self.stats.path_length_cuts += 1;
                continue;
            }
            if self.visits[w as usize] as usize >= self.limits.max_node_visits {
                self.stats.node_visit_cuts += 1;
                continue;
            }
            self.enter(w, 0, false);
            if self.abort {
                return;
            }
        }
    }

    /// EMIT (section 4.3) with the (path, start_offset) dedup guard (section 4.4).
    fn emit(&mut self, depth: usize) {
        let nodes = &self.graph.nodes;
        let mut path = String::new();
        for (i, &w) in self.walk.iter().enumerate() {
            if i > 0 {
                path.push('>');
            }
            path.push_str(&nodes[w as usize].id);
        }
        if !self.seen.insert((path.clone(), self.start_offset)) {
            self.dup_dropped += 1;
            return;
        }
        let colors = self.active[depth].clone();
        self.stats.candidates += 1;
        self.candidates.push(Candidate {
            path,
            start_offset: self.start_offset,
            length_nt: self.seq.len(),
            sequence: String::from_utf8_lossy(&self.seq).into_owned(),
            shared: !colors.is_empty(),
            colors,
        });
    }
}

#[cfg(test)]
mod tests;
