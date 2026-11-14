//! ColorFrame: bounded ORF enumeration over small coloured sequence graphs.
//! Pipeline: parse -> validate -> search -> write (ALGORITHM_SPEC.md, INPUT_OUTPUT_SCHEMA.md).

pub mod cli;
pub mod error;
pub mod graph;
pub mod output;
pub mod parse;
pub mod search;

use std::fs;
use std::time::Instant;

use error::{CfError, USAGE};
use output::GraphRun;

fn read_input(path: &str) -> Result<String, CfError> {
    let bytes =
        fs::read(path).map_err(|e| CfError::new(USAGE, format!("cannot read '{path}': {e}")))?;
    Ok(String::from_utf8_lossy(&bytes).into_owned())
}

fn write_output(path: &str, content: &str) -> Result<(), CfError> {
    fs::write(path, content).map_err(|e| CfError::new(USAGE, format!("cannot write '{path}': {e}")))
}

fn ms(start: Instant, end: Instant) -> f64 {
    end.duration_since(start).as_secs_f64() * 1000.0
}

/// Run the whole pipeline for one configuration.
pub fn run(cfg: &cli::Config) -> Result<(), CfError> {
    let t0 = Instant::now();

    // parse: read files and split into rows
    let nodes_text = read_input(&cfg.nodes)?;
    let edges_text = read_input(&cfg.edges)?;
    let nodes = parse::parse_nodes(&nodes_text, &cfg.nodes);
    let edges = parse::parse_edges(&edges_text, &cfg.edges);
    let t1 = Instant::now();

    // validate: schema order, builds the graphs (no output on error)
    let graphs = graph::validate(&nodes, &edges, &cfg.nodes, &cfg.edges)?;
    let t2 = Instant::now();

    // search: graphs ascending, policies in byte order
    let mut runs = Vec::new();
    for g in &graphs {
        for &policy in &cfg.policies {
            let result = search::search(g, policy, &cfg.limits);
            runs.push(GraphRun {
                graph_id: g.id.clone(),
                policy,
                result,
            });
        }
    }
    let t3 = Instant::now();

    // write
    write_output(&cfg.out, &output::render_candidates(&runs))?;
    write_output(&cfg.summary, &output::render_summary(&runs))?;
    let t4 = Instant::now();

    if let Some(path) = &cfg.timings {
        let rows = [
            ("parse", ms(t0, t1)),
            ("validate", ms(t1, t2)),
            ("search", ms(t2, t3)),
            ("write", ms(t3, t4)),
            ("total", ms(t0, t4)),
        ];
        write_output(path, &output::render_timings(&rows))?;
    }
    Ok(())
}
