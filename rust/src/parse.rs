//! Parsing of nodes.tsv / edges.tsv into rows (syntax-level checks only).
//! Rows are kept with the first syntax error so that `graph::validate` can report
//! errors in the exact order required by INPUT_OUTPUT_SCHEMA.md section 2.
use crate::error::{CfError, INVALID_COLORS, INVALID_DNA, INVALID_ID, MALFORMED_INPUT};

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
    !s.is_empty()
        && s.bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'.' || b == b'-')
}

pub fn is_valid_dna(s: &str) -> bool {
    !s.is_empty() && s.bytes().all(|b| matches!(b, b'A' | b'C' | b'G' | b'T'))
}

const MAX_COLOR: u64 = 2_147_483_647;

/// `.` -> empty set; otherwise strictly ascending non-negative ints, no leading zeros, <= 2^31-1.
pub fn parse_colors(s: &str) -> Option<Vec<u32>> {
    if s == "." {
        return Some(Vec::new());
    }
    let mut out: Vec<u32> = Vec::new();
    for tok in s.split(',') {
        let t = tok.as_bytes();
        if t.is_empty() || t.len() > 10 || !t.iter().all(u8::is_ascii_digit) {
            return None;
        }
        if t.len() > 1 && t[0] == b'0' {
            return None; // leading zero
        }
        let v: u64 = tok.parse().ok()?;
        if v > MAX_COLOR {
            return None;
        }
        let v = v as u32;
        if out.last().is_some_and(|&last| v <= last) {
            return None; // not strictly ascending
        }
        out.push(v);
    }
    Some(out)
}

/// `-?[0-9]+` fitting in i64.
pub fn parse_overlap(s: &str) -> Option<i64> {
    let digits = s.strip_prefix('-').unwrap_or(s);
    if digits.is_empty() || !digits.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    s.parse().ok()
}

/// Split into lines; one trailing newline is optional. Blank lines are kept (and rejected later).
fn split_lines(text: &str) -> Vec<&str> {
    if text.is_empty() {
        return Vec::new();
    }
    text.strip_suffix('\n')
        .unwrap_or(text)
        .split('\n')
        .collect()
}

fn malformed(file: &str, line: usize, what: &str) -> CfError {
    CfError::new(MALFORMED_INPUT, format!("{file}:{line}: {what}"))
}

/// Check the header line; returns the data lines with their 1-based line numbers.
fn check_header<'a>(
    text: &'a str,
    file: &str,
    expected: &str,
) -> Result<Vec<(usize, &'a str)>, CfError> {
    let lines = split_lines(text);
    match lines.first() {
        Some(h) if *h == expected => {}
        Some(h) => {
            return Err(malformed(
                file,
                1,
                &format!("expected header '{expected}', found '{h}'"),
            ))
        }
        None => return Err(malformed(file, 1, "missing header")),
    }
    Ok(lines
        .into_iter()
        .enumerate()
        .skip(1)
        .map(|(i, l)| (i + 1, l))
        .collect())
}

fn parse_node_line(line: usize, text: &str, file: &str) -> Result<NodeRow, CfError> {
    if text.is_empty() {
        return Err(malformed(file, line, "blank line"));
    }
    let f: Vec<&str> = text.split('\t').collect();
    if f.len() != 4 {
        return Err(malformed(
            file,
            line,
            &format!("expected 4 fields, found {}", f.len()),
        ));
    }
    for (name, v) in [("graph_id", f[0]), ("node_id", f[1])] {
        if !is_valid_id(v) {
            return Err(CfError::new(
                INVALID_ID,
                format!("{file}:{line}: invalid {name} '{v}'"),
            ));
        }
    }
    if !is_valid_dna(f[2]) {
        return Err(CfError::new(
            INVALID_DNA,
            format!("{file}:{line}: invalid sequence '{}'", f[2]),
        ));
    }
    let colors = parse_colors(f[3]).ok_or_else(|| {
        CfError::new(
            INVALID_COLORS,
            format!("{file}:{line}: invalid colors '{}'", f[3]),
        )
    })?;
    Ok(NodeRow {
        line,
        graph_id: f[0].to_string(),
        node_id: f[1].to_string(),
        sequence: f[2].as_bytes().to_vec(),
        colors,
    })
}

fn parse_edge_line(line: usize, text: &str, file: &str) -> Result<EdgeRow, CfError> {
    if text.is_empty() {
        return Err(malformed(file, line, "blank line"));
    }
    let f: Vec<&str> = text.split('\t').collect();
    if f.len() != 4 {
        return Err(malformed(
            file,
            line,
            &format!("expected 4 fields, found {}", f.len()),
        ));
    }
    for (name, v) in [("graph_id", f[0]), ("source", f[1]), ("target", f[2])] {
        if !is_valid_id(v) {
            return Err(CfError::new(
                INVALID_ID,
                format!("{file}:{line}: invalid {name} '{v}'"),
            ));
        }
    }
    let overlap = parse_overlap(f[3]).ok_or_else(|| {
        malformed(
            file,
            line,
            &format!("overlap_nt '{}' is not an integer", f[3]),
        )
    })?;
    Ok(EdgeRow {
        line,
        graph_id: f[0].to_string(),
        source: f[1].to_string(),
        target: f[2].to_string(),
        overlap,
    })
}

fn parse_rows<T>(
    text: &str,
    file: &str,
    header: &str,
    parse_line: fn(usize, &str, &str) -> Result<T, CfError>,
) -> Parsed<T> {
    let mut rows = Vec::new();
    let lines = match check_header(text, file, header) {
        Ok(l) => l,
        Err(e) => {
            return Parsed {
                rows,
                error: Some(e),
            }
        }
    };
    for (line, l) in lines {
        match parse_line(line, l, file) {
            Ok(r) => rows.push(r),
            Err(e) => {
                return Parsed {
                    rows,
                    error: Some(e),
                }
            }
        }
    }
    Parsed { rows, error: None }
}

pub fn parse_nodes(text: &str, file: &str) -> Parsed<NodeRow> {
    parse_rows(
        text,
        file,
        "graph_id\tnode_id\tsequence\tcolors",
        parse_node_line,
    )
}

pub fn parse_edges(text: &str, file: &str) -> Parsed<EdgeRow> {
    parse_rows(
        text,
        file,
        "graph_id\tsource\ttarget\toverlap_nt",
        parse_edge_line,
    )
}

#[cfg(test)]
mod tests;
