//! Bounded depth-first ORF search (ALGORITHM_SPEC.md section 4).
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

/// `local` (bases available from the start offset, up to 3) must be a prefix of "ATG".
pub fn start_frame_allowed(local: &[u8]) -> bool {
    let _ = local;
    todo!()
}

pub fn is_stop_codon(codon: &[u8]) -> bool {
    let _ = codon;
    todo!()
}

/// Intersection of two sorted slices into `out` (cleared first).
pub fn intersect_sorted(a: &[u32], b: &[u32], out: &mut Vec<u32>) {
    let _ = (a, b, out);
    todo!()
}

pub fn search(graph: &Graph, policy: Policy, limits: &Limits) -> SearchResult {
    let _ = (graph, policy, limits);
    todo!()
}

#[cfg(test)]
mod tests;
