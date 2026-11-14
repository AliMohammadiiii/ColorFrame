//! Byte-exact TSV output (INPUT_OUTPUT_SCHEMA.md section 4).
use crate::search::{Policy, SearchResult};

pub struct GraphRun {
    pub graph_id: String,
    pub policy: Policy,
    pub result: SearchResult,
}

pub const CANDIDATE_HEADER: &str =
    "graph_id\tpolicy\tcandidate_id\tpath\tstart_offset\tlength_nt\tsequence\tsupport_colors\tstatus\n";
pub const SUMMARY_HEADER: &str = "graph_id\tpolicy\tsearch_states\tmax_depth\tcandidates\tstart_rejected\tcolor_pruned\tdead_ends\torf_length_cuts\tpath_length_cuts\tnode_visit_cuts\tstate_limit_hit\texhaustive\n";

/// Runs must already be in (graph_id, policy) order; candidate_id is the rank within a run.
pub fn render_candidates(runs: &[GraphRun]) -> String {
    let _ = runs;
    todo!()
}

pub fn render_summary(runs: &[GraphRun]) -> String {
    let _ = runs;
    todo!()
}

/// `phase\tms` header then one row per phase, 3 decimals.
pub fn render_timings(rows: &[(&str, f64)]) -> String {
    let _ = rows;
    todo!()
}

#[cfg(test)]
mod tests;
