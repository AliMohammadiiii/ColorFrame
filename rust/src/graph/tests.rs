use super::*;
use crate::error::*;
use crate::parse::{parse_edges, parse_nodes};

const NH: &str = "graph_id\tnode_id\tsequence\tcolors\n";
const EH: &str = "graph_id\tsource\ttarget\toverlap_nt\n";

pub fn build(nodes: &str, edges: &str) -> Result<Vec<Graph>, CfError> {
    let n = parse_nodes(&format!("{NH}{nodes}"), "nodes.tsv");
    let e = parse_edges(&format!("{EH}{edges}"), "edges.tsv");
    validate(&n, &e, "nodes.tsv", "edges.tsv")
}

fn err_code(nodes: &str, edges: &str) -> &'static str {
    build(nodes, edges).unwrap_err().code
}

#[test]
fn graph_construction_sorts_nodes_and_successors() {
    let gs = build(
        "g2\tz\tA\t.\ng1\tb\tACGT\t1\ng1\ta\tACGT\t1\ng1\tc\tACGT\t.\n",
        "g1\ta\tc\t0\ng1\ta\tb\t0\n",
    )
    .unwrap();
    assert_eq!(gs.len(), 2);
    assert_eq!(gs[0].id, "g1");
    assert_eq!(gs[1].id, "g2");
    let ids: Vec<&str> = gs[0].nodes.iter().map(|n| n.id.as_str()).collect();
    assert_eq!(ids, ["a", "b", "c"]);
    assert_eq!(gs[0].nodes[0].succ, vec![1, 2]);
    assert_eq!(gs[0].overlap, 0);
}

#[test]
fn startable_range_excludes_overlap_when_node_has_successors() {
    let gs = build(
        "g\ta\tCCATG\t.\ng\tb\tATGAA\t.\n",
        "g\ta\tb\t3\n",
    )
    .unwrap();
    let g = &gs[0];
    assert_eq!(g.overlap, 3);
    assert_eq!(g.startable_end(0), 2); // 5 - K
    assert_eq!(g.startable_end(1), 5); // sink: all positions
}

#[test]
fn overlap_bounds() {
    assert_eq!(err_code("g\ta\tACG\t.\ng\tb\tACG\t.\n", "g\ta\tb\t3\n"), INVALID_OVERLAP); // >= len(target)
    assert_eq!(err_code("g\ta\tAC\t.\ng\tb\tACGT\t.\n", "g\ta\tb\t3\n"), INVALID_OVERLAP); // > len(source)
    assert_eq!(err_code("g\ta\tAC\t.\ng\tb\tACGT\t.\n", "g\ta\tb\t-1\n"), INVALID_OVERLAP);
    assert!(build("g\ta\tAC\t.\ng\tb\tACGT\t.\n", "g\ta\tb\t2\n").is_ok());
}

#[test]
fn overlap_mismatch() {
    assert_eq!(err_code("g\ta\tATGCCC\t.\ng\tb\tGGGTAA\t.\n", "g\ta\tb\t2\n"), OVERLAP_MISMATCH);
}

#[test]
fn inconsistent_overlap_between_edges() {
    let nodes = "g\ta\tAAAA\t.\ng\tb\tAAAA\t.\ng\tc\tAAAA\t.\n";
    assert_eq!(err_code(nodes, "g\ta\tb\t1\ng\tb\tc\t2\n"), INCONSISTENT_OVERLAP);
}

#[test]
fn node_and_edge_reference_errors() {
    assert_eq!(err_code("g\ta\tA\t.\ng\ta\tC\t.\n", ""), DUPLICATE_NODE);
    assert_eq!(err_code("g\ta\tA\t.\n", "g\ta\tb\t0\n"), MISSING_NODE);
    assert_eq!(err_code("g\ta\tA\t.\n", "h\ta\ta\t0\n"), MISSING_NODE);
    let two = "g\ta\tAC\t.\ng\tb\tAC\t.\n";
    assert_eq!(err_code(two, "g\ta\tb\t0\ng\ta\tb\t0\n"), DUPLICATE_EDGE);
}

#[test]
fn self_loop_allowed() {
    let gs = build("g\ta\tACGT\t.\n", "g\ta\ta\t0\n").unwrap();
    assert_eq!(gs[0].nodes[0].succ, vec![0]);
}

#[test]
fn node_errors_win_over_edge_errors() {
    // nodes.tsv defects are reported before any edge defect.
    let n = parse_nodes(&format!("{NH}g\ta\tAC\t.\ng\ta\tAC\t.\n"), "nodes.tsv");
    let e = parse_edges(&format!("{EH}g\ta\tz\tx\n"), "edges.tsv");
    let r = validate(&n, &e, "nodes.tsv", "edges.tsv").unwrap_err();
    assert_eq!(r.code, DUPLICATE_NODE);
}
