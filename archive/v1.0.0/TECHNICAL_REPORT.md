# ColorFrame — Technical Report

**Algorithmic trade-offs and cross-language performance of frame-aware candidate path search
in coloured sequence graphs**

Project lead: Ali Mohammadi · Report date: 2026-11-14 · Spec v1.0 · Release v1.0.0

Authoritative data: `results/modal/20261114T181422Z` (commit `bdd1d4f`, clean tree), analysed
in `reports/figures/modal_20261114T181422Z/`. Memory reference: `results/local/20261114T181117Z`
(macOS, same implementation code), analysed in `reports/figures/local_20261114T181117Z/`.

---

## 1. Motivation

Single-cell metagenomics can produce up to millions of incomplete bacterial genomes, typically
summarised as a coloured de Bruijn graph in which each node records the cells (colours) it was
observed in. Annotating such a graph raises four algorithmic questions that this project turns
into a small, fully specified experiment:

1. How do you find coding regions by walking a branching graph when you cannot follow every
   branch?
2. What happens with cycles and repeats, and is a loop *in frame*?
3. When may evidence from different cells be combined?
4. How do you make this fast without losing correctness?

ColorFrame is deliberately a toy model (see `LIMITATIONS.md`). Its value lies in the precision
of the question and the trustworthiness of the measurements, not in biological realism.

## 2. Method

### 2.1 Model (`ALGORITHM_SPEC.md`)

Nodes carry DNA and a colour set; edges carry one overlap `K` per graph (as in a compacted de
Bruijn graph). A depth-first search starts at every owned position whose local bases are a
prefix of `ATG`. It extends walks base by base, tracks the frame implicitly (codon boundaries are
every third base from the start) and stops a walk at the first in-frame stop codon. Four bounds
keep it finite: ORF length, walk length, visits per node and total states. Every bound that cuts
the search is counted, and `exhaustive = 0` is reported whenever one did.

Two support policies:

- **strict**: keep a walk only while some colour is shared by every node so far;
- **permissive**: keep a walk while every node has *some* colour, and label candidates without a
  shared colour as `fragmented_support`.

### 2.2 How cycles and loop frames are handled

Nothing special is done, and nothing needs to be. Because the frame is derived from the
spelled length, a loop whose spelled length is ≡ 0 (mod 3) preserves the frame and one that is
not shifts it on every traversal. Fixture **G11** makes this concrete: a 4-nt loop shifts the
frame by one per lap, and the downstream stop codon becomes in-frame only after two laps, which
the bounded search finds (and loses when revisits are forbidden, B09). Termination comes from the
bounds; the visit bound is what limits how many times a repeat may be re-entered (G07, G08).

### 2.3 Engineering and verification

| Layer | Evidence |
|---|---|
| Ground truth | 39 cases with hand-derived expected outputs; candidate sets cross-checked by an independent brute-force oracle (`tests/check_fixtures.py`) |
| Conformance | Python, C++17 and Rust each pass 39/39 byte-for-byte, on macOS/clang and Linux/GCC (in the benchmark container) |
| Equivalence | identical `candidates.tsv` and `summary.tsv` across languages on all 20 generated workloads (up to 56 264 candidates or 800 000 search states per workload), checked again inside the container before timing |
| Unit tests | 42 (Python), 165 checks (C++), 41 (Rust); `cargo clippy -D warnings`, `-Werror` |
| Process | TDD order visible in Git (`test:` before `feat:` on each branch); every defect found became a fixture correction or a fix commit (D-014, generator fix) |

Two hand-derived summary expectations turned out to be wrong (B09, B10). Both were caught by the
implementations, which stopped and escalated instead of editing the fixtures, and were then
corrected by hand-checking against the specification (D-014).

### 2.4 Benchmark protocol (`BENCHMARK_PROTOCOL.md`)

- Modal container: `cpu=1.0`, 4 GiB, Debian, Python 3.12.10, GCC 12.2.0, Rust 1.99.1, AMD CPU at
  2.45 GHz.
- 2 warm-up runs and 7 measured runs per implementation and workload, in randomised order;
  medians with interquartile ranges.
- Main metric: the in-process `search_ms`. `wall_ms` also includes interpreter start-up.
- The Modal sandbox reports a floor of about 51 MB for child peak RSS, so **memory is taken from
  the local macOS run** (D-015).

## 3. Results

### RQ1 — Support policies (`rq1_*`, 500 nodes, 100 planted ORFs)

Each planted ORF comes from four "true" cells; every node of its walk is observed in each of them
with probability *p*.

| p | strict recovered | permissive recovered | strict candidates | permissive candidates | fragmented |
|---:|---:|---:|---:|---:|---:|
| 0.1 | 1 | 9 | 86 | 230 | 144 |
| 0.2 | 6 | 35 | 218 | 654 | 436 |
| 0.3 | 18 | 63 | 368 | 1201 | 833 |
| 0.5 | 59 | 95 | 839 | 1978 | 1139 |
| 0.7 | 91 | 99 | 1261 | 2744 | 1483 |
| 0.9 | 100 | 100 | 1971 | 2923 | 952 |

![RQ1](figures/modal_20261114T181422Z/fig4_rq1_policies.png)

- **Each policy reaches its theoretical ceiling.** Strict recovered exactly the planted ORFs with
  a colour shared by all their nodes, and permissive exactly those whose every node had some
  colour, at every *p* (and on the large `perf` graphs: 559/559 and 933/933). The search never
  loses a planted ORF to its bounds; the policy alone decides.
- **The price of permissiveness is output volume.** At *p* = 0.3, permissive recovers 3.5× more
  planted ORFs (63 vs 18) but emits 3.3× more candidates, and 69% of them (833) have no shared
  colour. In sparse data the strict policy is safe but blind; the permissive one sees more but
  needs a downstream filter.
- The gap closes as coverage rises: at *p* = 0.9 both recover everything.

This is the quantitative form of the question "when can evidence safely be shared across cells?"
Sharing (permissive) is what makes recovery possible at low coverage, and the `fragmented_support`
label marks exactly the candidates that depend on it.

### RQ2 — Implementations (Modal, median search time)

| Workload | Python | C++17 | Rust | C++ speed-up | Rust speed-up | Rust/C++ |
|---|---:|---:|---:|---:|---:|---:|
| perf_n50_low | 2.99 ms | 0.14 ms | 0.11 ms | 21.5× | 27.5× | 1.28 |
| perf_n500_high | 61.2 ms | 3.37 ms | 2.99 ms | 18.2× | 20.5× | 1.13 |
| perf_n10000_high | 1374 ms | 89.3 ms | 80.7 ms | 15.4× | 17.0× | 1.11 |
| rq1_p50 | 67.8 ms | 3.67 ms | 3.58 ms | 18.4× | 18.9× | 1.03 |
| stress_s800000 | 10 370 ms | 124.5 ms | 100.4 ms | 83.3× | 103.3× | 1.24 |

Variability is small: 40 of the 60 (workload, implementation) rows have a relative IQR below 3%,
and the largest is 14%, on a 0.11 ms search (`runtime_summary.tsv`). Over all 20 workloads the
compiled implementations are 15–29× faster than Python on the `perf` graphs, 15–39× on the `rq1`
graphs and 82–104× on the stress workload. Rust is faster than C++ on 19 of 20 workloads (1.03–1.40×). The exception is the
smallest (`perf_n50_high`, 0.83×), where search takes about 0.1 ms.

**Why stress widens the gap (interpretation, not profiled).** Stress walks never emit candidates
and never fail the colour gate, so the run is almost pure per-base loop work, which is what an
interpreter handles worst. On the graph workloads, candidate construction, string building and
sorting take a larger share of the work.

**End-to-end** on small inputs is a different story: on `perf_n50_low` the Python wall time is
43 ms against a 3 ms search, because the rest is interpreter start-up.

**Compiler sensitivity.** On macOS/clang the Rust/C++ ratio on `stress_s800000` is about 2.3
(93 vs 214 ms), against 1.24 on Linux/GCC. The relative performance of the two compiled
implementations depends on the toolchain, so environments are never pooled.

### RQ3 — Trade-offs

![scaling](figures/modal_20261114T181422Z/fig1_scaling_search_time.png)
![stress](figures/modal_20261114T181422Z/fig2_stress_state_limit.png)

- **Size:** search time grows roughly linearly with node count in both branching regimes. The
  generated graphs are acyclic with local edges, and random sequence has a stop codon about every
  21 codons, so most walks are short and the bounds rarely bind.
- **Branching:** going from out-degree 1.2 to 2.0 multiplies search time by 1.8–3.0×, depending
  on implementation and size (Python 2.0×, C++ 2.8×, Rust 3.0× at 10 000 nodes). Why the
  compiled implementations are affected more was not profiled.
  The walk-length bound binds only in permissive searches on the larger graphs (n ≥ 2000, both
  branching regimes), which are therefore reported with `exhaustive = 0`; strict searches on
  `perf` graphs are always exhaustive.
- **State limit:** on the cycle-heavy stress graph every walk ends at a bound, the state limit
  binds, and time is linear in the limit (throughput constant per implementation: Python ≈ 0.08,
  C++ ≈ 6.4, Rust ≈ 8.0 million states/s). The state limit is therefore a direct
  time-versus-completeness knob, and the output says when it was used.
- **Memory** (macOS, peak RSS, whole process):

  | Workload | Python | C++17 | Rust |
  |---|---:|---:|---:|
  | stress_s800000 (no candidates) | 18.4 MB | 2.4 MB | 2.5 MB |
  | perf_n500_high | 22.2 MB | 5.3 MB | 5.0 MB |
  | perf_n10000_high (56 264 candidates) | 111.5 MB | 80.2 MB | 51.2 MB |

  Traversal itself uses almost no memory (walk + one ORF buffer). Memory is dominated by the
  interpreter baseline for Python and by stored candidate records on large outputs. Why C++
  uses more than Rust on the largest output was not profiled.

### RQ4 — AI-assisted development effort

| | Python | C++17 | Rust |
|---|---:|---:|---:|
| Recorded agent tokens (completed legs only) | 108 958 | 116 682 | 126 251 |
| Agent restarts after API errors | 1 | 1 | 2 |
| Conformance runs failed before pass | 1 (fixture errors) | 1 (fixture errors) | 0 |
| Median search, stress_s800000 | 10 370 ms | 124 ms | 100 ms |

The recorded token counts differ by about 15%, while performance differs by up to 100×.
**No relationship between development effort and performance can be claimed.** Every
implementation lost at least one leg whose usage was not exposed. Rust lost the leg in which it
wrote most of its code, so its recorded figure is mostly verification. There is one development
history per language (n = 1). What the data does support:

- All three implementations reached byte-identical behaviour against one frozen specification
  without a single implementation defect found by the conformance suite. Python and C++ each had
  one failing run, caused by two errors in the hand-written fixtures (not in their code); Rust,
  started after the fixture fix, passed on its first run. For this problem the specification and
  fixtures, not the language, carried most of the correctness burden.
- The coordinating effort (specification, fixtures, oracle, review, measurement) is shared and
  not exposed; it is plausibly the largest part of total AI usage.

## 4. Discussion

- **Frame-aware traversal is easy to get right once the frame is derived, not stored.**
  Deriving the frame from the spelled length removes a whole class of bugs. Loops, repeats and
  boundary-spanning codons need no special cases.
- **Branch choice.** This study enumerates rather than ranks; the RQ1 data suggests how a ranked
  search (for example beam search) should treat branches. A shared-colour branch is the
  high-precision choice, a fragmented branch the high-recall one, and a policy that keeps both
  but labels them preserves the decision for later evidence.
- **Scaling.** The exponential worst case shows up only on cycle-rich, stop-poor graphs, and
  there the state limit makes the cost predictable. A production system would need ranking,
  pruning by coding potential (e.g. a protein model), and partial-gene reporting.

## 5. Limitations

See `LIMITATIONS.md`. The most important: colours are local evidence, so even strict support does
not prove a full walk exists in one cell. Everything here is synthetic with a simple
independent-dropout model. Benchmarks describe these implementations on these machines. RQ4 is
an n = 1 case study with incomplete telemetry.

## 6. Reproduction

```bash
make test                                  # all correctness checks, locally
modal run --detach benchmarks/modal_app.py # authoritative pipeline + R analysis
```

Details: `REPRODUCIBILITY.md`, `MODAL_EXECUTION.md`.
