//! Manual command-line parsing (INPUT_OUTPUT_SCHEMA.md section 3).
use crate::error::CfError;
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

/// `args` excludes the program name.
pub fn parse_args(args: &[String]) -> Result<Config, CfError> {
    let _ = args;
    todo!()
}

#[cfg(test)]
mod tests;
