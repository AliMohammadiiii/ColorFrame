//! Manual command-line parsing (INPUT_OUTPUT_SCHEMA.md section 3).
use crate::error::{CfError, USAGE};
use crate::search::{Limits, Policy};

#[derive(Debug, Clone)]
pub struct Config {
    pub nodes: String,
    pub edges: String,
    pub out: String,
    pub summary: String,
    pub timings: Option<String>,
    /// Policies in output (byte) order: permissive before strict.
    pub policies: Vec<Policy>,
    pub limits: Limits,
}

fn usage(msg: impl Into<String>) -> CfError {
    CfError::new(USAGE, msg)
}

/// Strict unsigned integer: digits only (no sign, no suffix), must fit usize and be >= min.
fn parse_limit(flag: &str, value: &str, min: usize) -> Result<usize, CfError> {
    if value.is_empty() || !value.bytes().all(|b| b.is_ascii_digit()) {
        return Err(usage(format!("{flag} expects an integer, got '{value}'")));
    }
    let n: usize = value
        .parse()
        .map_err(|_| usage(format!("{flag} value '{value}' is out of range")))?;
    if n < min {
        return Err(usage(format!("{flag} must be >= {min}, got {n}")));
    }
    Ok(n)
}

/// `args` excludes the program name.
pub fn parse_args(args: &[String]) -> Result<Config, CfError> {
    let mut nodes = None;
    let mut edges = None;
    let mut out = None;
    let mut summary = None;
    let mut timings = None;
    let mut policy: Option<String> = None;
    let mut limits = Limits::default();

    let mut it = args.iter();
    while let Some(flag) = it.next() {
        if !flag.starts_with("--") {
            return Err(usage(format!("unexpected argument '{flag}'")));
        }
        const KNOWN: [&str; 9] = [
            "--nodes",
            "--edges",
            "--out",
            "--summary",
            "--timings",
            "--policy",
            "--max-orf-nt",
            "--max-path-nodes",
            "--max-node-visits",
        ];
        if !KNOWN.contains(&flag.as_str()) && flag != "--max-states" {
            return Err(usage(format!("unknown flag '{flag}'")));
        }
        let value = it
            .next()
            .filter(|v| !v.starts_with("--"))
            .ok_or_else(|| usage(format!("flag {flag} requires a value")))?;
        match flag.as_str() {
            "--nodes" => nodes = Some(value.clone()),
            "--edges" => edges = Some(value.clone()),
            "--out" => out = Some(value.clone()),
            "--summary" => summary = Some(value.clone()),
            "--timings" => timings = Some(value.clone()),
            "--policy" => policy = Some(value.clone()),
            "--max-orf-nt" => limits.max_orf_nt = parse_limit(flag, value, 6)?,
            "--max-path-nodes" => limits.max_path_nodes = parse_limit(flag, value, 1)?,
            "--max-node-visits" => limits.max_node_visits = parse_limit(flag, value, 1)?,
            _ => limits.max_states = parse_limit(flag, value, 1)?,
        }
    }

    let need = |v: Option<String>, flag: &str| {
        v.ok_or_else(|| usage(format!("missing required flag {flag}")))
    };
    let policy = need(policy, "--policy")?;
    // Output order is by policy name bytes: permissive < strict.
    let policies = match policy.as_str() {
        "strict" => vec![Policy::Strict],
        "permissive" => vec![Policy::Permissive],
        "both" => vec![Policy::Permissive, Policy::Strict],
        other => {
            return Err(usage(format!(
                "invalid --policy '{other}' (expected strict, permissive or both)"
            )))
        }
    };
    Ok(Config {
        nodes: need(nodes, "--nodes")?,
        edges: need(edges, "--edges")?,
        out: need(out, "--out")?,
        summary: need(summary, "--summary")?,
        timings,
        policies,
        limits,
    })
}

#[cfg(test)]
mod tests;
