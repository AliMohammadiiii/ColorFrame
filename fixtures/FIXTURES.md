# Fixtures: hand-derived ground truth

**Status:** Validated — every expected candidate set below was derived by hand from
`ALGORITHM_SPEC.md` and then cross-checked by an independent brute-force oracle
(`tests/oracle_bruteforce.py`, run by `tests/check_fixtures.py`). The oracle enumerates walks
first and scans them afterwards, a different formulation from the DFS. Summary counters were
derived by hand only (the oracle does not model traversal order); the implementations are then
required to reproduce them.

Layout: `fixtures/cases/<CASE>/{nodes.tsv, edges.tsv, args.txt}` plus either
`expected_candidates.tsv` + `expected_summary.tsv` or `expected_error.txt`.
Default limits unless `args.txt` overrides: ORF ≤ 1200 nt, walk ≤ 12 nodes, ≤ 2 visits per
node, ≤ 50 000 states. `K` is the graph's uniform overlap.

Design rule: filler is built from `C`/`G` so that every `ATG` and every stop codon is placed
deliberately. Node-boundary junctions were checked for accidental `ATG`s.

## Functional scenarios (charter §6.1)

| Case | Graph (K) | What it tests | Expected |
|---|---|---|---|
| G01 | `n1=CCATGCCCGCCTAACC` | single-node ORF | `n1` @2, `ATG CCC GCC TAA` (12 nt). 1 state. |
| G02 | `n1=CCATGCCG → n2=CCGGCCGCC → n3=GCCTAACC` (K=3) | overlap bases not duplicated | `n1>n2>n3` @2, `ATG CCG GCC GCC TAA` (15). Spelled = `n1 + n2[3:] + n3[3:]`. Support {1,2}∩{1,2}∩{1} = {1}. |
| G03 | `n1=CCCCAT → {n2=GCCCTGACC, n3=CCTAACC}` | start codon `AT|G` across boundary | `n1>n2` @4, `ATG CCC TGA` (9). Via `n3` the first codon is `ATC` → `start_rejected=1`. |
| G04 | `n1=ATGCTAACCTAGCCCTAACC → n2=GGG` | first **in-frame** stop wins | `n1` @0, `ATG CTA ACC TAG` (12). The out-of-frame `TAA` at 4–6 is ignored; `n2` is never entered (1 state). |
| G05 | `n1=CCATGCCC → {n2=GGGTAACC, n3=GGTAACCC}` | one coding branch, one non-coding | `n1>n2` @2 (12 nt). `n1>n3` reads `GGT AAC CC`, no stop → `dead_ends=1`. |
| G06 | `n1=ATGCCC{1,2} → {n2=GCCTAACC{1}, n3=GGGCCCTGACC{2}}` | keep both valid branches | `n1>n2` (12, support 1) and `n1>n3` (15, support 2). |
| G07 | `n1=ATGCCC → n2=GCCGCC ⇄ n3=CGGCCG` | directed cycle, stop-free, in-frame (6 nt per node) | 0 candidates; walk `n1 n2 n3 n2 n3` then `n2` refused by the visit bound → `node_visit_cuts=1`, `exhaustive=0`. Terminates after 5 states. |
| G08 | `n1=ATGCCC → r=GCC → {n3=CTAACC, x=GG}`, `x → r` | repeat that must be revisited | Direct `n1>r>n3` reads `CTA ACC` (dead end). Detour through `x` (+5 nt, frame shift 2) puts `TAA` in frame: `n1>r>x>r>n3` (18). 7 states. |
| G09 | `n1{1} → n2{1,2} → {n3{2}, n4{1}, n5{.}}` | strict vs permissive | strict: only `n1>n2>n4` (support 1); `n3` pruned (∩ empty), `n5` pruned. permissive: adds `n1>n2>n3` as `fragmented_support` (support `.`); `n5` pruned (no local colour). |
| G10 | `n1=ATGCCC → n2=GGGTAA`, overlap 2 | invalid overlap | `ERROR OVERLAP_MISMATCH` (`CC` ≠ `GG`), exit 2. |
| G11 | `n1=ATGCCC → {e=CTAACC, l=GCCG}`, `l → l`, `l → e` | **loop length not divisible by 3** (frame-shifting loop) | `l` adds 4 nt, shifting the frame by 1 per traversal. `e` entered at phase 0 (`CTA ACC`) and phase 1 (`?CT AAC C`) has no stop; at phase 2 (after two traversals) `C|TAA` is in frame: `n1>l>l>e` (18). |

G11 is the direct answer to "is a loop in frame or not?": the frame is determined by the spelled
loop length modulo 3, and the bounded search finds the stop codon that only becomes in-frame
after a specific number of traversals.

## Boundary scenarios

| Case | Input | Expected |
|---|---|---|
| B01 | empty graph (headers only) | header-only outputs, exit 0 |
| B02 | `CCCGGGCCC` | no start → 0 states, exhaustive |
| B03 | `ATGCCCGGG` | no stop → `dead_ends=1`, 0 candidates |
| B04 | G01, `--max-orf-nt 9` | ORF open at 9 nt → `orf_length_cuts=1`, not exhaustive |
| B05 | G01, `--max-orf-nt 12` | ORF of exactly 12 nt is still emitted (stop check precedes cut) |
| B06 | G06, `--max-states 2` | `n1`, `n1>n2` (emitted), limit hit before `n3`; 1 candidate, `state_limit_hit=1` |
| B07 | G02, `--max-path-nodes 2` | `n3` refused → `path_length_cuts=1`, 0 candidates |
| B08 | G08, `--max-node-visits 1` | the revisit candidate is lost; `node_visit_cuts=1` |
| B09 | G11, `--max-node-visits 1` | the frame-shift candidate is lost |
| B10 | `ATGTAA` with colours `.` | pruned under both policies (`color_pruned=1`) |
| B11 | all valid G graphs in one file, input in reverse order | outputs sorted by `graph_id` |
| B12/B13 | G09 with `--policy strict` / `permissive` | single-policy output |

## Invalid-input scenarios (one defect each)

| Case | Defect | Code |
|---|---|---|
| E01 / E02 / E03 | `ATGNCC` / lower case / empty sequence | `INVALID_DNA` |
| E04 | duplicate node id | `DUPLICATE_NODE` |
| E05 / E06 | edge to unknown node / unknown graph | `MISSING_NODE` |
| E07 | duplicate edge | `DUPLICATE_EDGE` |
| E08 / E09 / E14 | overlap = len(target) / > len(source) / negative | `INVALID_OVERLAP` |
| E10 | overlaps 2 and 1 in one graph | `INCONSISTENT_OVERLAP` |
| E11 / E12 | colours `2,1` / `1,x` | `INVALID_COLORS` |
| E13 | node id `n>1` (would break path syntax) | `INVALID_ID` |
| E15 | overlap `x` | `MALFORMED_INPUT` |

## Worked derivation: G08 (repeat)

Exploration order (successors sorted: `n3` < `x`):

| # | Enter | Walk | len(seq) after node | Event |
|---|---|---|---:|---|
| 1 | n1 @0 | n1 | 6 | `ATG CCC` |
| 2 | r | n1 r | 9 | `GCC` |
| 3 | n3 | n1 r n3 | 15 | `CTA ACC`, no successors → dead end |
| 4 | x | n1 r x | 11 | |
| 5 | r (2nd) | n1 r x r | 14 | codon `GGG` |
| 6 | n3 | n1 r x r n3 | 18 | `CCC TAA` → **emit** |
| 7 | x (2nd) | n1 r x r x | 16 | codon `CCG`; child `r` refused (2 visits) → `node_visit_cuts=1` |

Summary: 7 states, depth 5, 1 candidate, 1 dead end, 1 visit cut, not exhaustive.
