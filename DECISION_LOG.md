# Decision Log

Format: decision · alternatives · reason · consequences · date · responsible.
"Ali" = project lead; "dev agent" = Claude Opus 5.5 acting as development coordinator under
Ali's direction. Entries marked *proposed by dev agent* are engineering refinements within the
scope Ali set; they do not change the research questions.

---

### D-001 — Authorship and naming policy for Git
- **Decision:** Commits are made with the repository owner's configured Git identity (Ali, the
  person accountable for the software). Branch names and commit messages contain no AI tool or
  model names. Which agent produced each commit is recorded in `AI_USAGE.md` (commit → agent
  table) and `results/agent_usage.csv`.
- **Alternatives:** `Co-Authored-By` trailers naming the model; per-agent Git identities.
- **Reason:** explicit instruction from Ali (2026-11-14). Transparency is preserved through the
  usage ledger rather than commit metadata.
- **Consequences:** `git log` alone does not show AI involvement; `AI_USAGE.md` is the
  authoritative attribution record and must be kept in sync.
- **Date / by:** 2026-11-14 · Ali (instruction), dev agent (implementation).

### D-002 — Uniform overlap per graph
- **Decision:** all edges of a graph must declare the same overlap `K` (`INCONSISTENT_OVERLAP`
  otherwise).
- **Alternatives:** per-edge arbitrary overlaps; per-source-node consistency.
- **Reason:** mirrors compacted de Bruijn graphs (`K = k − 1`) and makes start-position
  ownership (D-003) unambiguous. Per-edge overlaps let one spelled position belong to several
  nodes in walk-dependent ways.
- **Consequences:** generality is reduced; fixtures with `K = 0` and `K = 3` cover both regimes.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-003 — Start-position ownership
- **Decision:** in a node with successors, the last `K` positions are not startable; they are
  owned by the successors.
- **Alternatives:** allow all positions and deduplicate by sequence; attribute overlap starts to
  the upstream node.
- **Reason:** each ORF is reported once, attributed to the shortest walk that spells it. The
  shortest walk carries the fewest colour constraints, so strict support is not lost because of
  an unnecessary upstream node.
- **Consequences:** documented in `ALGORITHM_SPEC.md` §2.3; G02 exercises it.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-004 — Fully specified exploration order
- **Decision:** nodes by id (byte order), offsets ascending, successors by target id,
  depth-first; state limit applies per `(graph, policy)` and aborts immediately.
- **Alternatives:** unspecified order (compare only non-truncated runs).
- **Reason:** makes state-limited (truncated) runs comparable across languages — essential for
  cycle-heavy benchmark workloads where truncation is the normal case.
- **Consequences:** iterative implementations must reproduce the recursive order exactly.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-005 — Recursive DFS
- **Decision:** reference pseudocode is recursive; recursion depth ≤ `max_path_nodes` (12).
- **Alternatives:** explicit stack.
- **Reason:** clarity; depth is bounded, so no stack-overflow risk at default limits.
- **Consequences:** CLI rejects nothing about depth, but very large `--max-path-nodes` could hit
  Python's recursion limit; documented in `LIMITATIONS.md`.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-006 — Explicit counters and the meaning of `exhaustive`
- **Decision:** separate counters for natural outcomes (`dead_ends`, `color_pruned`,
  `start_rejected`) and for truncations (`orf_length_cuts`, `path_length_cuts`,
  `node_visit_cuts`, `state_limit_hit`). `exhaustive = 1` only if no truncation occurred.
- **Reason:** charter requirement that truncation is never reported as exhaustive; the counters
  also give RQ1/RQ3 their measurements and make cross-language comparison much stricter than
  comparing candidate counts.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-007 — Ground truth: hand derivation + independent oracle
- **Decision:** expected outputs are written as literals derived by hand; a brute-force oracle
  using a different formulation checks the candidate sets before any implementation exists.
- **Reason:** guards against hand-derivation mistakes without letting an implementation define
  its own expected output.
- **Consequences:** the oracle found no disagreement with the hand derivations; it caught one
  defect in the fixture *writer* (single-policy cases), fixed before commit.
- **Date / by:** 2026-11-14 · dev agent, for Ali's review.

### D-008 — Output schema extends the charter's minimal columns
- **Decision:** `candidates.tsv` adds `policy`, `start_offset`, `length_nt`, `support_colors`;
  statuses are `shared_support` / `fragmented_support`; a separate `summary.tsv` carries counters.
- **Reason:** `policy` and `start_offset` are needed to make records unique and comparable;
  `support_colors` makes the policy outcome inspectable.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-009 — `DESIGN.md` folded into `ARCHITECTURE.md`
- **Reason:** the two would duplicate each other at this project size.
- **Date / by:** 2026-11-14 · dev agent.

### D-010 — Generated workloads use `K = 0`; generator is Python only
- **Decision:** the benchmark generator emits overlap-0 graphs; overlap handling is covered by
  fixtures (G02, B07, E08–E10). One generator produces files read by all implementations.
- **Alternatives:** junction-label generator with `K > 0`.
- **Reason:** planting known ORFs across overlapping junctions without creating accidental
  codons would add generator complexity unrelated to the research questions.
- **Consequences:** benchmark numbers exclude the cost of overlap slicing (negligible: an offset).
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-011 — Every `ATG` yields its own candidate
- **Decision:** nested in-frame starts are separate candidates; no longest-ORF selection.
- **Reason:** keeps the traversal definition simple and policy-neutral; selection is a
  downstream annotation decision.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-012 — R analysis runs inside a pinned Modal container
- **Decision:** `analysis/analysis.R` runs in `rocker/r-ver` on Modal, base R graphics only.
- **Alternatives:** install R locally with Homebrew.
- **Reason:** R is not installed on the development machine; a pinned container is more
  reproducible than a local install and avoids modifying the workstation.
- **Date / by:** 2026-11-14 · dev agent.

### D-013 — Additional fixture G11 (frame-shifting loop)
- **Decision:** add G11 beyond the ten charter fixtures.
- **Reason:** directly tests whether a loop is "in frame": a 4-nt loop shifts the frame by one
  per traversal, and the stop codon becomes in-frame only after two traversals.
- **Date / by:** 2026-11-14 · proposed by dev agent.

### D-014 — Correction of two hand-derived summary expectations (B09, B10)
- **Decision:** correct `expected_summary.tsv` of B09 (`max_depth` 2 → 3) and B10
  (`search_states` 1 → 2, `color_pruned` 1 → 2). Candidate expectations were unchanged.
- **How found:** the Python implementation agent passed 37/39 cases and, as instructed, stopped
  and reported the two disagreements instead of editing fixtures. Re-derivation by hand from
  `ALGORITHM_SPEC.md` confirmed the report: in B09 `e` is re-entered at depth 3 after
  backtracking (`n1>l>e`); in B10 the trailing `A` of `ATGTAA` creates a second start frame
  (§4.2 note 2).
- **Why the oracle did not catch it:** `tests/check_fixtures.py` verifies candidate sets only;
  traversal counters are hand-derived. Counters are now independently confirmed by agreement
  between the hand derivation and the implementations.
- **Consequence:** B10 keeps its sequence because it now also exercises the trailing-`A` rule.
- **Date / by:** 2026-11-14 · dev agent (correction), reported by the Python implementation agent.
