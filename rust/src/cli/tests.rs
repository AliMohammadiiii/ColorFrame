use super::*;

fn args(s: &str) -> Vec<String> {
    s.split_whitespace().map(String::from).collect()
}

const BASE: &str = "--nodes n --edges e --out o --summary s --policy strict";

#[test]
fn minimal_valid_arguments_use_defaults() {
    let c = parse_args(&args(BASE)).unwrap();
    assert_eq!(c.nodes, "n");
    assert_eq!(c.policies, vec![Policy::Strict]);
    assert_eq!(c.limits, Limits::default());
    assert!(c.timings.is_none());
}

#[test]
fn both_policy_orders_permissive_first() {
    let c = parse_args(&args(
        "--nodes n --edges e --out o --summary s --policy both",
    ))
    .unwrap();
    assert_eq!(c.policies, vec![Policy::Permissive, Policy::Strict]);
}

#[test]
fn limits_and_timings() {
    let c = parse_args(&args(&format!(
        "{BASE} --timings t --max-orf-nt 9 --max-path-nodes 2 --max-node-visits 1 --max-states 7"
    )))
    .unwrap();
    assert_eq!(c.timings.as_deref(), Some("t"));
    assert_eq!(
        c.limits,
        Limits {
            max_orf_nt: 9,
            max_path_nodes: 2,
            max_node_visits: 1,
            max_states: 7
        }
    );
}

fn usage(s: &str) {
    let e = parse_args(&args(s)).unwrap_err();
    assert_eq!(e.code, "USAGE", "{s}");
    assert_eq!(e.exit_status(), 64);
}

#[test]
fn usage_errors() {
    usage("--nodes n --edges e --out o --summary s"); // missing policy
    usage("--edges e --out o --summary s --policy strict"); // missing nodes
    usage(&format!("{BASE} --bogus 1"));
    usage(&format!("{BASE} --max-states")); // no value
    usage(&format!("{BASE} --max-states x"));
    usage(&format!("{BASE} --max-states +1"));
    usage(&format!("{BASE} --max-states 99999999999999999999999"));
    usage(&format!("{BASE} --max-orf-nt 5")); // below minimum 6
    usage(&format!("{BASE} --max-path-nodes 0"));
    usage(&format!("{BASE} --max-node-visits 0"));
    usage(&format!("{BASE} --max-states 0"));
    usage("--nodes n --edges e --out o --summary s --policy weird");
    usage(&format!("{BASE} stray"));
}
