//! Graph model and semantic validation (ALGORITHM_SPEC.md section 2).
use crate::error::CfError;
use crate::parse::{EdgeRow, NodeRow, Parsed};

#[derive(Debug, Clone)]
pub struct Node {
    pub id: String,
    pub seq: Vec<u8>,
    /// Sorted ascending.
    pub colors: Vec<u32>,
    /// Successor node indices, sorted by target id (= by index, nodes are id-sorted).
    pub succ: Vec<u32>,
}

#[derive(Debug, Clone)]
pub struct Graph {
    pub id: String,
    /// Sorted by id (byte order).
    pub nodes: Vec<Node>,
    /// The uniform overlap K (0 when the graph has no edges).
    pub overlap: usize,
}

impl Graph {
    /// Exclusive end of the startable offsets of node `u` (section 2.3).
    pub fn startable_end(&self, u: usize) -> usize {
        let _ = u;
        todo!()
    }
}

/// Validate parsed input and build graphs sorted by graph_id.
pub fn validate(
    nodes: &Parsed<NodeRow>,
    edges: &Parsed<EdgeRow>,
    nodes_file: &str,
    edges_file: &str,
) -> Result<Vec<Graph>, CfError> {
    let _ = (nodes, edges, nodes_file, edges_file);
    todo!()
}

#[cfg(test)]
pub(crate) mod tests;
