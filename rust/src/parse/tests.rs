use super::*;

const NH: &str = "graph_id\tnode_id\tsequence\tcolors\n";
const EH: &str = "graph_id\tsource\ttarget\toverlap_nt\n";

#[test]
fn dna_validation() {
    assert!(is_valid_dna("ACGT"));
    assert!(is_valid_dna("A"));
    assert!(!is_valid_dna(""));
    assert!(!is_valid_dna("ACGN"));
    assert!(!is_valid_dna("acgt"));
}

#[test]
fn identifier_validation() {
    assert!(is_valid_id("n1"));
    assert!(is_valid_id("G-1.a_B"));
    assert!(!is_valid_id(""));
    assert!(!is_valid_id("n 1"));
    assert!(!is_valid_id("n>1"));
    assert!(!is_valid_id("n,1"));
}

#[test]
fn colour_parsing() {
    assert_eq!(parse_colors("."), Some(vec![]));
    assert_eq!(parse_colors("0"), Some(vec![0]));
    assert_eq!(parse_colors("1,2,7"), Some(vec![1, 2, 7]));
    assert_eq!(parse_colors("2147483647"), Some(vec![2147483647]));
    assert_eq!(parse_colors("2,1"), None);
    assert_eq!(parse_colors("1,1"), None);
    assert_eq!(parse_colors("1,x"), None);
    assert_eq!(parse_colors("01"), None);
    assert_eq!(parse_colors("+1"), None);
    assert_eq!(parse_colors("-1"), None);
    assert_eq!(parse_colors(""), None);
    assert_eq!(parse_colors("1,"), None);
    assert_eq!(parse_colors("2147483648"), None);
    assert_eq!(parse_colors("99999999999999999999"), None);
}

#[test]
fn overlap_parsing_is_strict() {
    assert_eq!(parse_overlap("0"), Some(0));
    assert_eq!(parse_overlap("-3"), Some(-3));
    assert_eq!(parse_overlap("+1"), None);
    assert_eq!(parse_overlap("1x"), None);
    assert_eq!(parse_overlap(""), None);
    assert_eq!(parse_overlap("-"), None);
    assert_eq!(parse_overlap("9223372036854775808"), None);
}

#[test]
fn nodes_rows_and_optional_trailing_newline() {
    let p = parse_nodes(&format!("{NH}g\tn1\tACGT\t1,2\ng\tn2\tTT\t."), "nodes.tsv");
    assert!(p.error.is_none());
    assert_eq!(p.rows.len(), 2);
    assert_eq!(p.rows[0].sequence, b"ACGT".to_vec());
    assert_eq!(p.rows[0].colors, vec![1, 2]);
    assert!(p.rows[1].colors.is_empty());
    assert_eq!(p.rows[1].line, 3);
}

#[test]
fn nodes_error_codes_in_check_order() {
    let code = |row: &str| {
        parse_nodes(&format!("{NH}{row}\n"), "nodes.tsv")
            .error
            .map(|e| e.code)
    };
    assert_eq!(code("g\tn1\tACGT"), Some(MALFORMED_INPUT));
    assert_eq!(code("g\tn1\tACGT\t.\textra"), Some(MALFORMED_INPUT));
    assert_eq!(code("g x\tn1\tACGT\t."), Some(INVALID_ID));
    assert_eq!(code("g\tn1\tACGN\t."), Some(INVALID_DNA));
    assert_eq!(code("g\tn1\t\t."), Some(INVALID_DNA));
    assert_eq!(code("g\tn1\tACGT\t2,1"), Some(INVALID_COLORS));
    assert_eq!(code("g\tn1\tACGT\t."), None);
}

#[test]
fn blank_line_and_bad_header_are_malformed() {
    let p = parse_nodes(&format!("{NH}\ng\tn1\tA\t.\n"), "nodes.tsv");
    assert_eq!(p.error.unwrap().code, MALFORMED_INPUT);
    let p = parse_nodes("graph_id\tnode\tsequence\tcolors\n", "nodes.tsv");
    assert_eq!(p.error.unwrap().code, MALFORMED_INPUT);
    let p = parse_nodes("", "nodes.tsv");
    assert_eq!(p.error.unwrap().code, MALFORMED_INPUT);
}

#[test]
fn edge_rows_and_errors() {
    let p = parse_edges(&format!("{EH}g\ta\tb\t2\n"), "edges.tsv");
    assert!(p.error.is_none());
    assert_eq!(p.rows[0].overlap, 2);
    let code = |row: &str| {
        parse_edges(&format!("{EH}{row}\n"), "edges.tsv")
            .error
            .map(|e| e.code)
    };
    assert_eq!(code("g\ta\tb"), Some(MALFORMED_INPUT));
    assert_eq!(code("g\ta b\tb\t0"), Some(INVALID_ID));
    assert_eq!(code("g\ta\tb\tx"), Some(MALFORMED_INPUT));
    assert_eq!(code("g\ta\tb\t+1"), Some(MALFORMED_INPUT));
    assert_eq!(code("g\ta\tb\t-1"), None); // negative is a validation (not parse) error
    assert!(parse_edges(EH, "edges.tsv").rows.is_empty());
}
