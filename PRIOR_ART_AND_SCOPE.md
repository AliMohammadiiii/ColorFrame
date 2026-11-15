# Prior Art and Scope

**Status:** Validated for v1.0.1 (ggCaller workflow verified from the full text).

## ColorFrame versus ggCaller

| Aspect | ggCaller (Horsfield et al. 2023) | ColorFrame |
|---|---|---|
| Graph | Bifrost coloured compacted DBG built from assemblies | hand-made or synthetic directed sequence graph with explicit node sequences and one declared overlap `K`; no graph construction |
| ORF discovery | DFS from stop codons, pairing stops in the same reading frame | DFS from every owned `ATG`, ending at the first in-frame stop |
| Path validity | FM-index query against the input sequences removes walks that no input contains ("short-circuits") | **none**: any walk allowed by the bounds is a candidate |
| Colour evidence | number of colours shared in a node, used in start scoring | strict (one colour on every node) or permissive (some colour on each node) pruning policies |
| Start selection | scored by translation-initiation context, colour coverage and orthologue consistency | none: every `ATG` yields its own candidate |
| Downstream | COG clustering, Balrog scoring, functional annotation | none |
| Validation | simulated and real bacterial populations | synthetic fixtures and workloads only; no biological validation |
| Engineering focus | a production tool | a fully specified traversal, explicit truncation accounting, three byte-equivalent implementations |

## Not claimed as new

Graph-based ORF discovery, frame-aware DFS, colour-based evidence, bounded path enumeration and
the ATG-to-first-stop ORF definition are all established (see `LITERATURE_REVIEW.md`).

## What ColorFrame contributes

1. **A precise, testable problem statement.** The spec defines start ownership under overlaps,
   exploration order, and a counter for every pruning and truncation event, so independent
   implementations can be compared byte for byte.
2. **Truncation as an output.** `exhaustive = 0` whenever a bound hid part of the walk space.
3. **A controlled synthetic comparison of two colour-support policies (RQ1).** Planted ORFs carry
   known true samples, with explicit true-observation and spurious-colour processes and 10 paired
   replicates.
4. **An engineering case study (RQ2–RQ3):** three implementations under one semantic contract,
   with equivalent timing phases, in one pinned environment.
5. **A descriptive record of the AI-assisted development process.**

## Explicitly not claimed

- That ColorFrame finds genes, or that a recovered candidate is a validated gene.
- That colour support, strict or permissive, proves a walk exists in any single cell.
- That results transfer to real coloured DBGs, real single-cell data or genome scale.
- That one programming language is faster in general. Results describe these implementations,
  with their language-idiomatic data structures, on the recorded hardware.
- Any relationship between AI token use and code quality or performance.
