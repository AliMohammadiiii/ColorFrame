# Limitations

**Status:** Validated against the implemented system.

## Scientific

1. **Colours are local evidence, not proof.** A node's colour means the sequence was observed in
   that sample. Even under the strict policy, a shared colour on every node does not prove that
   the complete walk exists contiguously in that sample (two paths can share all nodes'
   colours yet be spliced differently in the sample). A strictly supported candidate is not a
   confirmed gene.
2. **Permissive candidates are hypotheses.** `fragmented_support` means every node was seen
   somewhere, but no single sample covers the walk; such candidates may be chimeras.
3. **Simplified graph model.** No k-mer graph construction, uniform overlap only, forward strand
   only, `ATG` starts only, no coding-potential scoring, no frameshift tolerance, no partial
   (start-less or stop-less) genes. In sparse single-cell data most genes are partial, so v1
   reports only a subset of what a real annotator would need.
4. **Nested starts.** Every in-frame `ATG` yields its own candidate; no longest-ORF or start
   selection is made (D-011).
5. **Loops and repeats.** Cycles are handled only through the bounds. The frame effect of a loop
   (its spelled length mod 3) is captured implicitly, as G11 shows, but repeat copy number cannot
   be inferred from the graph, so a walk through a repeat is a possibility, not a reconstruction.
6. **Synthetic data.** All results come from synthetic graphs (≤ 10 000 nodes) and a simple
   independent-dropout model of per-cell evidence. Nothing is validated against real data.

## Engineering

7. **Exponential worst case.** Bounded DFS is exponential in `max_path_nodes` on branching
   graphs; the state limit keeps it total, at the cost of incompleteness (`exhaustive = 0`).
8. **State-limit results depend on exploration order.** They are reproducible because the order
   is fully specified (D-004), but a different order would keep a different subset.
9. **Recursion.** All implementations recurse to depth `max_path_nodes`; extreme values could
   exhaust the stack (D-005). Python raises its recursion limit accordingly.
10. **C++ review note (still applicable).** `expand()` keeps a reference into the per-depth colour buffer vector,
    which deeper calls may reallocate. It is not used after the recursive calls, so it is
    correct today, but it is fragile under refactoring.
11. **Benchmarks** describe these idiomatic implementations (different colour-set representations, `ALGORITHM_SPEC.md` §5a) on one Modal CPU configuration whose model the sandbox does not report. Vertex ids are sorted, and sensitivity to id permutation and generator seed was **not** tested; synthetic topology and ordering can distort graph benchmarks (Mehrotra et al. 2024).
11a. **No path validation.** ggCaller removes walks not present in any input with an FM-index; ColorFrame has no equivalent, so even strict candidates may be graph artefacts.
11b. **RQ1 model.** Independent per-(node, sample) observation and spurious-colour draws; real dropout is correlated with coverage, cell and genome position.

## Process

12. **API interruptions.** Most agent legs were cut off by an account spend limit or a network
    error. Their token usage was not exposed and is recorded as `NOT_EXPOSED`, so per-language
    totals are lower bounds and RQ4 comparisons are only indicative.
13. **One development history per language** (n = 1). RQ4 is a case study, not an experiment.
