//! ColorFrame: bounded ORF enumeration over small coloured sequence graphs.
//! Pipeline: parse -> validate -> search -> write (ALGORITHM_SPEC.md, INPUT_OUTPUT_SCHEMA.md).

pub mod cli;
pub mod error;
pub mod graph;
pub mod output;
pub mod parse;
pub mod search;

use std::time::Instant;

use error::{CfError, USAGE};

/// Run the whole pipeline for one configuration.
pub fn run(cfg: &cli::Config) -> Result<(), CfError> {
    let _ = cfg;
    todo!()
}

#[allow(dead_code)]
fn _unused(_: Instant, _: &str) {
    let _ = USAGE;
}
