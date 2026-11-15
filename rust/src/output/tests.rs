use super::*;
use crate::search::{Candidate, Stats};

fn cand(path: &str, off: usize, colors: Vec<u32>) -> Candidate {
    Candidate {
        path: path.into(),
        start_offset: off,
        length_nt: 6,
        sequence: "ATGTAA".into(),
        shared: !colors.is_empty(),
        colors,
    }
}

fn run(policy: Policy, cands: Vec<Candidate>) -> GraphRun {
    let stats = Stats {
        search_states: 3,
        max_depth: 2,
        candidates: cands.len() as u64,
        ..Stats::default()
    };
    GraphRun {
        graph_id: "g".into(),
        policy,
        result: SearchResult {
            candidates: cands,
            stats,
            dup_dropped: 0,
        },
    }
}

#[test]
fn candidates_have_header_ranks_and_dot_for_empty_colours() {
    let runs = vec![run(
        Policy::Permissive,
        vec![cand("a>b", 1, vec![1, 5]), cand("c", 0, vec![])],
    )];
    let s = render_candidates(&runs);
    assert_eq!(
        s,
        format!(
            "{CANDIDATE_HEADER}g\tpermissive\t1\ta>b\t1\t6\tATGTAA\t1,5\tshared_support\n\
             g\tpermissive\t2\tc\t0\t6\tATGTAA\t.\tfragmented_support\n"
        )
    );
}

#[test]
fn empty_output_is_header_only() {
    assert_eq!(render_candidates(&[]), CANDIDATE_HEADER);
    assert_eq!(render_summary(&[]), SUMMARY_HEADER);
}

#[test]
fn summary_row_format() {
    let s = render_summary(&[run(Policy::Strict, vec![])]);
    assert_eq!(
        s,
        format!("{SUMMARY_HEADER}g\tstrict\t3\t2\t0\t0\t0\t0\t0\t0\t0\t0\t1\n")
    );
}

#[test]
fn timings_format() {
    let s = render_timings(&[("parse", 1.0), ("total", 2.34567)]);
    assert_eq!(s, "phase\tms\nparse\t1.000\ntotal\t2.346\n");
}

#[test]
fn canonicalize_orders_runs_and_candidates() {
    // Spec v1.1: runs arrive in execution order (strict first) with candidates in emission order.
    let unsorted = || vec![cand("a>c", 0, vec![1]), cand("a>b", 4, vec![1])];
    let mut runs = vec![
        run(Policy::Strict, unsorted()),
        run(Policy::Permissive, unsorted()),
    ];
    canonicalize(&mut runs);
    assert_eq!(runs[0].policy, Policy::Permissive);
    for r in &runs {
        let got: Vec<(&str, usize)> = r
            .result
            .candidates
            .iter()
            .map(|c| (c.path.as_str(), c.start_offset))
            .collect();
        assert_eq!(got, vec![("a>b", 4), ("a>c", 0)]);
    }
}
