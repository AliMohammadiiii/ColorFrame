//! Graph model and semantic validation (ALGORITHM_SPEC.md section 2).
use std::collections::{BTreeMap, HashMap, HashSet};

use crate::error::{
    CfError, DUPLICATE_EDGE, DUPLICATE_NODE, INCONSISTENT_OVERLAP, INVALID_OVERLAP, MISSING_NODE,
    OVERLAP_MISMATCH,
};
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
        let n = &self.nodes[u];
        if n.succ.is_empty() {
            n.seq.len()
        } else {
            n.seq.len() - self.overlap
        }
    }
}

/// Per-graph builder: nodes in file order, edges as (source, target) indices.
#[derive(Default)]
struct Builder {
    nodes: Vec<(String, Vec<u8>, Vec<u32>)>,
    index: HashMap<String, usize>,
    edges: Vec<(usize, usize)>,
    edge_set: HashSet<(usize, usize)>,
    overlap: Option<i64>,
}

/// Validate parsed input (order: INPUT_OUTPUT_SCHEMA.md section 2) and build graphs
/// sorted by graph_id with id-sorted nodes and sorted successor lists.
pub fn validate(
    nodes: &Parsed<NodeRow>,
    edges: &Parsed<EdgeRow>,
    nodes_file: &str,
    edges_file: &str,
) -> Result<Vec<Graph>, CfError> {
    let mut builders: BTreeMap<String, Builder> = BTreeMap::new();

    // 1. node rows in file order (syntax errors of later rows come after earlier rows' checks)
    for r in &nodes.rows {
        let b = builders.entry(r.graph_id.clone()).or_default();
        if b.index.contains_key(&r.node_id) {
            return Err(CfError::new(
                DUPLICATE_NODE,
                format!(
                    "{nodes_file}:{}: duplicate node '{}' in graph '{}'",
                    r.line, r.node_id, r.graph_id
                ),
            ));
        }
        b.index.insert(r.node_id.clone(), b.nodes.len());
        b.nodes
            .push((r.node_id.clone(), r.sequence.clone(), r.colors.clone()));
    }
    if let Some(e) = &nodes.error {
        return Err(e.clone());
    }

    // 2. edge rows in file order
    for r in &edges.rows {
        let missing = |what: &str, id: &str| {
            CfError::new(
                MISSING_NODE,
                format!(
                    "{edges_file}:{}: {what} '{id}' not found in graph '{}'",
                    r.line, r.graph_id
                ),
            )
        };
        let b = builders
            .get_mut(&r.graph_id)
            .ok_or_else(|| missing("graph", &r.graph_id))?;
        let s = *b
            .index
            .get(&r.source)
            .ok_or_else(|| missing("source", &r.source))?;
        let t = *b
            .index
            .get(&r.target)
            .ok_or_else(|| missing("target", &r.target))?;
        if !b.edge_set.insert((s, t)) {
            return Err(CfError::new(
                DUPLICATE_EDGE,
                format!(
                    "{edges_file}:{}: duplicate edge '{}' -> '{}' in graph '{}'",
                    r.line, r.source, r.target, r.graph_id
                ),
            ));
        }
        let (src, tgt) = (&b.nodes[s].1, &b.nodes[t].1);
        let ov = r.overlap;
        if ov < 0 || ov as u64 > src.len() as u64 || ov as u64 >= tgt.len() as u64 {
            return Err(CfError::new(
                INVALID_OVERLAP,
                format!(
                    "{edges_file}:{}: overlap {ov} outside [0, len(source)] / below len(target)",
                    r.line
                ),
            ));
        }
        let ovu = ov as usize;
        if src[src.len() - ovu..] != tgt[..ovu] {
            return Err(CfError::new(
                OVERLAP_MISMATCH,
                format!(
                    "{edges_file}:{}: suffix of '{}' != prefix of '{}' for overlap {ov}",
                    r.line, r.source, r.target
                ),
            ));
        }
        // Remember the first overlap; a differing one is reported in step 3.
        b.edges.push((s, t));
        if b.overlap.is_none() {
            b.overlap = Some(ov);
        } else if b.overlap != Some(ov) {
            b.overlap = Some(-1); // sentinel: inconsistent
        }
    }
    if let Some(e) = &edges.error {
        return Err(e.clone());
    }

    // 3. per graph (ascending id): uniform overlap
    for (gid, b) in &builders {
        if b.overlap == Some(-1) {
            return Err(CfError::new(
                INCONSISTENT_OVERLAP,
                format!("{edges_file}: graph '{gid}' declares different overlaps"),
            ));
        }
    }

    Ok(builders.into_iter().map(|(id, b)| finish(id, b)).collect())
}

/// Sort nodes by id and remap edge indices.
fn finish(id: String, b: Builder) -> Graph {
    let mut order: Vec<usize> = (0..b.nodes.len()).collect();
    order.sort_by(|&x, &y| b.nodes[x].0.cmp(&b.nodes[y].0));
    let mut new_index = vec![0u32; order.len()];
    for (new, &old) in order.iter().enumerate() {
        new_index[old] = new as u32;
    }
    let mut nodes: Vec<Node> = order
        .iter()
        .map(|&old| {
            let (nid, seq, colors) = &b.nodes[old];
            Node {
                id: nid.clone(),
                seq: seq.clone(),
                colors: colors.clone(),
                succ: Vec::new(),
            }
        })
        .collect();
    for &(s, t) in &b.edges {
        nodes[new_index[s] as usize].succ.push(new_index[t]);
    }
    for n in &mut nodes {
        n.succ.sort_unstable();
    }
    Graph {
        id,
        nodes,
        overlap: b.overlap.map_or(0, |o| o as usize),
    }
}

#[cfg(test)]
pub(crate) mod tests;
