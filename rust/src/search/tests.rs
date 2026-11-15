use super::*;
use crate::graph::tests::build;

fn graph(nodes: &str, edges: &str) -> Graph {
    build(nodes, edges).unwrap().remove(0)
}

fn run(nodes: &str, edges: &str, policy: Policy, limits: Limits) -> SearchResult {
    search(&graph(nodes, edges), policy, &limits)
}

fn paths(r: &SearchResult) -> Vec<(String, usize)> {
    r.candidates
        .iter()
        .map(|c| (c.path.clone(), c.start_offset))
        .collect()
}

#[test]
fn colour_intersection() {
    let mut out = vec![99];
    intersect_sorted(&[1, 2, 5, 9], &[2, 3, 5, 10], &mut out);
    assert_eq!(out, vec![2, 5]);
    intersect_sorted(&[1], &[2], &mut out);
    assert!(out.is_empty());
    intersect_sorted(&[], &[2], &mut out);
    assert!(out.is_empty());
}

#[test]
fn start_frame_creation_rule() {
    assert!(start_frame_allowed(b"ATG"));
    assert!(start_frame_allowed(b"AT"));
    assert!(start_frame_allowed(b"A"));
    assert!(!start_frame_allowed(b"ATC"));
    assert!(!start_frame_allowed(b"TG"));
    assert!(!start_frame_allowed(b"CAT"));
}

#[test]
fn stop_codon_detection() {
    for s in [b"TAA", b"TAG", b"TGA"] {
        assert!(is_stop_codon(s));
    }
    for s in [b"ATG", b"TTA", b"GAT"] {
        assert!(!is_stop_codon(s));
    }
}

#[test]
fn single_node_orf_record() {
    let r = run(
        "g\tn1\tCCATGCCCGCCTAACC\t1,3\n",
        "",
        Policy::Strict,
        Limits::default(),
    );
    assert_eq!(r.candidates.len(), 1);
    let c = &r.candidates[0];
    assert_eq!(c.path, "n1");
    assert_eq!(c.start_offset, 2);
    assert_eq!(c.length_nt, 12);
    assert_eq!(c.sequence, "ATGCCCGCCTAA");
    assert_eq!(c.colors, vec![1, 3]);
    assert!(c.shared);
    assert_eq!(r.stats.search_states, 1);
    assert_eq!(r.stats.candidates, 1);
    assert!(r.stats.exhaustive());
}

#[test]
fn every_stop_codon_ends_the_orf() {
    for stop in ["TAA", "TAG", "TGA"] {
        let nodes = format!("g\tn\tCCATGCCC{stop}CC\t1\n");
        let r = run(&nodes, "", Policy::Strict, Limits::default());
        assert_eq!(r.candidates.len(), 1, "{stop}");
        assert_eq!(r.candidates[0].length_nt, 9);
    }
}

#[test]
fn first_in_frame_stop_wins_and_out_of_frame_is_ignored() {
    let r = run(
        "g\tn\tATGCTAACCTAGCCCTAACC\t1\n",
        "",
        Policy::Strict,
        Limits::default(),
    );
    assert_eq!(r.candidates.len(), 1);
    assert_eq!(r.candidates[0].sequence, "ATGCTAACCTAG");
}

#[test]
fn start_codon_spanning_nodes_is_detected_and_rejected_when_not_atg() {
    // a=CAT, b=GAAATAA: offset 1 of a gives "AT" -> frame; first codon ATG across boundary.
    let r = run(
        "g\ta\tCAT\t1\ng\tb\tGAAATAA\t1\n",
        "g\ta\tb\t0\n",
        Policy::Strict,
        Limits::default(),
    );
    assert_eq!(paths(&r), vec![("a>b".to_string(), 1)]);
    assert_eq!(r.candidates[0].sequence, "ATGAAATAA");
    // a=AT, b=CAAA: first codon ATC -> start_rejected.
    let r = run(
        "g\ta\tAT\t1\ng\tb\tCAAA\t1\n",
        "g\ta\tb\t0\n",
        Policy::Strict,
        Limits::default(),
    );
    assert!(r.candidates.is_empty());
    assert_eq!(r.stats.start_rejected, 1);
}

#[test]
fn single_base_a_at_node_end_creates_a_dead_end_frame() {
    let r = run("g\ta\tCCA\t1\n", "", Policy::Strict, Limits::default());
    assert_eq!(r.stats.search_states, 1);
    assert_eq!(r.stats.dead_ends, 1);
}

#[test]
fn frame_tracking_across_nodes_with_overlap() {
    // K=2: spelled = CCATGAA + GTAGG; ORF ATG AAG TAG from offset 2.
    let r = run(
        "g\ta\tCCATGAA\t1,2\ng\tb\tAAGTAGG\t2,3\n",
        "g\ta\tb\t2\n",
        Policy::Strict,
        Limits::default(),
    );
    assert_eq!(paths(&r), vec![("a>b".to_string(), 2)]);
    assert_eq!(r.candidates[0].sequence, "ATGAAGTAG");
    assert_eq!(r.candidates[0].length_nt, 9);
    assert_eq!(r.candidates[0].colors, vec![2]);
}

#[test]
fn strict_prunes_and_permissive_reports_fragmented_support() {
    let nodes = "g\ta\tATGAAA\t1\ng\tb\tTAA\t2\n";
    let edges = "g\ta\tb\t0\n";
    let s = run(nodes, edges, Policy::Strict, Limits::default());
    assert!(s.candidates.is_empty());
    // b is pruned from the frame at a@0 and from the trailing-A frame at a@5
    assert_eq!(s.stats.color_pruned, 2);
    let p = run(nodes, edges, Policy::Permissive, Limits::default());
    assert_eq!(p.candidates.len(), 1);
    assert!(!p.candidates[0].shared);
    assert!(p.candidates[0].colors.is_empty());
}

#[test]
fn node_without_colours_is_pruned_under_both_policies() {
    for pol in [Policy::Strict, Policy::Permissive] {
        let r = run("g\ta\tATGTAA\t.\n", "", pol, Limits::default());
        assert!(r.candidates.is_empty());
        // start frames: ATG at 0 and the trailing A at 5 (a one-base prefix of ATG)
        assert_eq!(r.stats.color_pruned, 2);
        assert_eq!(r.stats.search_states, 2);
    }
}

#[test]
fn cycle_terminates_by_visit_bound() {
    let r = run(
        "g\ta\tATGC\t1\n",
        "g\ta\ta\t0\n",
        Policy::Strict,
        Limits::default(),
    );
    assert!(r.candidates.is_empty());
    assert_eq!(r.stats.search_states, 2);
    assert_eq!(r.stats.max_depth, 2);
    assert_eq!(r.stats.node_visit_cuts, 1);
    assert!(!r.stats.exhaustive());
}

#[test]
fn path_length_bound_cuts() {
    let lim = Limits {
        max_path_nodes: 1,
        ..Limits::default()
    };
    let r = run("g\ta\tATGC\t1\n", "g\ta\ta\t0\n", Policy::Strict, lim);
    assert_eq!(r.stats.search_states, 1);
    assert_eq!(r.stats.path_length_cuts, 1);
    assert_eq!(r.stats.node_visit_cuts, 0);
}

#[test]
fn bounded_revisit_finds_candidate_only_when_allowed() {
    // x=ATGA loops; detour x>x>y shifts frame: x>y = ATGAAATAA is in frame.
    let nodes = "g\tx\tATGA\t1\ng\ty\tAATAA\t1\n";
    let edges = "g\tx\tx\t0\ng\tx\ty\t0\n";
    let r = run(nodes, edges, Policy::Strict, Limits::default());
    assert!(paths(&r).contains(&("x>y".to_string(), 0)));
    assert_eq!(r.stats.node_visit_cuts, 1); // third x refused
    let lim = Limits {
        max_node_visits: 1,
        ..Limits::default()
    };
    let r = run(nodes, edges, Policy::Strict, lim);
    assert!(paths(&r).contains(&("x>y".to_string(), 0)));
    assert!(r.stats.node_visit_cuts >= 1);
    assert!(r.candidates.iter().all(|c| c.path != "x>x>y"));
}

#[test]
fn orf_length_cut_and_exact_limit() {
    let nodes = "g\tn\tATGAAATAA\t1\n";
    let r = run(
        nodes,
        "",
        Policy::Strict,
        Limits {
            max_orf_nt: 6,
            ..Limits::default()
        },
    );
    assert!(r.candidates.is_empty());
    assert_eq!(r.stats.orf_length_cuts, 1);
    // stop at exactly the limit is still emitted
    let r = run(
        nodes,
        "",
        Policy::Strict,
        Limits {
            max_orf_nt: 9,
            ..Limits::default()
        },
    );
    assert_eq!(r.candidates.len(), 1);
    assert_eq!(r.stats.orf_length_cuts, 0);
}

#[test]
fn state_limit_aborts_immediately_keeping_earlier_candidates() {
    // a>b emits; a limit of 2 states stops before c is entered.
    let nodes0 = "g\ta\tATGCCC\t1,2\ng\tb\tGCCTAACC\t1\ng\tc\tGGGCCCTGACC\t2\n";
    let edges0 = "g\ta\tb\t0\ng\ta\tc\t0\n";
    let r = run(
        nodes0,
        edges0,
        Policy::Strict,
        Limits {
            max_states: 2,
            ..Limits::default()
        },
    );
    assert!(r.stats.state_limit_hit);
    assert_eq!(r.stats.search_states, 2);
    assert_eq!(paths(&r), vec![("a>b".to_string(), 0)]);
    assert!(!r.stats.exhaustive());
}

#[test]
fn candidates_sorted_and_no_duplicates() {
    let nodes = "g\ta\tATGCCC\t1,2\ng\tb\tGCCTAACC\t1\ng\tc\tGGGCCCTGACC\t2\n";
    let edges = "g\ta\tb\t0\ng\ta\tc\t0\n";
    let r = run(nodes, edges, Policy::Permissive, Limits::default());
    let p = paths(&r);
    let mut sorted = p.clone();
    sorted.sort();
    assert_eq!(p, sorted);
    assert_eq!(p.len(), 2);
    assert_eq!(r.dup_dropped, 0);
}

#[test]
fn search_returns_candidates_in_emission_order() {
    // Spec v1.1: sorting belongs to the canonicalize phase, not to search.
    let r = run(
        "G\ta\tATGCATGC\t1\nG\tb\tCCTAA\t1\nG\tc\tATAA\t1\n",
        "G\ta\tb\t0\nG\ta\tc\t0\n",
        Policy::Strict,
        Limits::default(),
    );
    assert_eq!(paths(&r), vec![("a>c".to_string(), 0), ("a>b".to_string(), 4)]);
}
