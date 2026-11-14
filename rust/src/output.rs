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
    let mut out = String::from(CANDIDATE_HEADER);
    for run in runs {
        for (i, c) in run.result.candidates.iter().enumerate() {
            let colors = if c.colors.is_empty() {
                ".".to_string()
            } else {
                c.colors
                    .iter()
                    .map(u32::to_string)
                    .collect::<Vec<_>>()
                    .join(",")
            };
            let status = if c.shared {
                "shared_support"
            } else {
                "fragmented_support"
            };
            out.push_str(&format!(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n",
                run.graph_id,
                run.policy.name(),
                i + 1,
                c.path,
                c.start_offset,
                c.length_nt,
                c.sequence,
                colors,
                status
            ));
        }
    }
    out
}

pub fn render_summary(runs: &[GraphRun]) -> String {
    let mut out = String::from(SUMMARY_HEADER);
    for run in runs {
        let s = &run.result.stats;
        out.push_str(&format!(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n",
            run.graph_id,
            run.policy.name(),
            s.search_states,
            s.max_depth,
            s.candidates,
            s.start_rejected,
            s.color_pruned,
            s.dead_ends,
            s.orf_length_cuts,
            s.path_length_cuts,
            s.node_visit_cuts,
            u8::from(s.state_limit_hit),
            u8::from(s.exhaustive())
        ));
    }
    out
}

/// `phase\tms` header then one row per phase, 3 decimals.
pub fn render_timings(rows: &[(&str, f64)]) -> String {
    let mut out = String::from("phase\tms\n");
    for (name, ms) in rows {
        out.push_str(&format!("{name}\t{ms:.3}\n"));
    }
    out
}

#[cfg(test)]
mod tests;
