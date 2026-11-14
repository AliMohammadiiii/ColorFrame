# Prior Art and Scope

**Status:** Validated.

## Not claimed as new

| Idea | Established by (examples) |
|---|---|
| Colour sets on graph nodes | Iqbal et al. 2012; Holley & Melsted 2020 |
| Gene calling by traversing a sequence graph | Horsfield et al. 2023 (ggCaller) |
| Making the reading frame explicit during graph construction or traversal | Peng et al. 2016; Jaromczyk et al. 2012 |
| ORF = ATG … first in-frame stop | standard textbook definition |
| Bounding path enumeration on cyclic graphs | standard algorithmic practice |

## What ColorFrame contributes

1. **A precise, testable problem statement.** Spec v1.0 defines start-position ownership under
   overlaps, exploration order, and a counter for every pruning and truncation event, so that
   independent implementations can be compared byte for byte.
2. **Truncation is a first-class output.** `exhaustive = 0` whenever a bound hides part of
   the walk space. A bounded search is never reported as complete.
3. **A controlled policy comparison (RQ1)** with known planted ORFs and a simple dropout model
   of sparse per-cell evidence.
4. **An engineering case study (RQ2–RQ4):** three byte-equivalent implementations, benchmarked
   in one pinned environment, with the AI-assisted development effort recorded alongside.

## Explicitly not claimed

- That ColorFrame finds genes. It enumerates ORF candidates in a toy model.
- That results transfer to real coloured de Bruijn graphs, real single-cell data, or genome
  scale. The synthetic graphs have at most 10 000 nodes.
- That one programming language is faster in general. Results describe *these*
  implementations, on *this* hardware, for *this* algorithm.
- That lower AI token usage means better engineering.
