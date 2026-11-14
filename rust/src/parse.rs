//! Parsing of nodes.tsv / edges.tsv into rows (syntax-level checks only).
//! Rows are kept with the first syntax error so that `graph::validate` can report
//! errors in the exact order required by INPUT_OUTPUT_SCHEMA.md section 2.
use crate::error::CfError;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NodeRow {
    pub line: usize,
    pub graph_id: String,
    pub node_id: String,
    pub sequence: Vec<u8>,
    pub colors: Vec<u32>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EdgeRow {
    pub line: usize,
    pub graph_id: String,
    pub source: String,
    pub target: String,
    pub overlap: i64,
}

/// Result of parsing one file: the rows before the first syntax error, plus that error.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parsed<T> {
    pub rows: Vec<T>,
    pub error: Option<CfError>,
}

pub fn is_valid_id(s: &str) -> bool {
    let _ = s;
    todo!()
}

pub fn is_valid_dna(s: &str) -> bool {
    let _ = s;
    todo!()
}

/// `.` -> empty set; otherwise strictly ascending non-negative ints, no leading zeros, <= 2^31-1.
pub fn parse_colors(s: &str) -> Option<Vec<u32>> {
    let _ = s;
    todo!()
}

/// `-?[0-9]+` fitting in i64.
pub fn parse_overlap(s: &str) -> Option<i64> {
    let _ = s;
    todo!()
}

pub fn parse_nodes(text: &str, file: &str) -> Parsed<NodeRow> {
    let _ = (text, file);
    todo!()
}

pub fn parse_edges(text: &str, file: &str) -> Parsed<EdgeRow> {
    let _ = (text, file);
    todo!()
}

#[cfg(test)]
mod tests;
