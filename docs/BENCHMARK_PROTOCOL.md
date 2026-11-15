# Benchmark Protocol

**Status:** Validated (v1.0.1). Authoritative run `results/modal/20261115T065950Z`. Earlier runs are superseded and labelled.

Phase boundaries: `INPUT_OUTPUT_SCHEMA.md` §4 (contract-tested). `--policy both` runs strict, then permissive, in every implementation. Comparisons are of these idiomatic implementations under one semantic contract (`ALGORITHM_SPEC.md` §5a). Timed workloads: perf (10), stress (4), and RQ1 replicate 0 clean (6); all 134 workloads are equivalence-checked.

## 1. Preconditions

1. All three implementations pass the 39 conformance cases (`tests/run_cases.py --impl all`).
2. All three produce byte-identical `candidates.tsv` and `summary.tsv` on every workload
   (`tests/cross_language.py`). Both run inside the benchmark container before timing starts.
3. Every measured run's output digest is recorded; a workload is flagged if digests differ
   between implementations or repetitions.

## 2. Workloads (`benchmarks/generate_workloads.py`, base seed 42)

| Family | Workloads | Purpose |
|---|---|---|
| `perf_n{50,200,500}_{low,high}` | charter grid: 3 sizes × out-degree 1.2 / 2.0, acyclic | RQ2, RQ3 |
| `perf_n{2000,10000}_{low,high}` | extension sizes for scaling | RQ3 |
| `stress_s{12500,50000,200000,800000}` | 200 nodes, out-degree 2, cycles, stop-free sequence; state limit swept | RQ3 throughput, limit interaction |
| `rq1_p{10,20,30,50,70,90}` | 500 nodes, out-degree 2, 100 planted ORFs, per-sample observation probability p | RQ1 |

Limits: defaults except `--max-states` (1 000 000 for `perf`/`rq1`, so the state limit never
binds; swept for `stress`). Every workload records its parameters, realised statistics and
input checksums in `params.json` / `metadata.json`.

## 3. Procedure

- Environment: one Modal container, `cpu=1.0`, 4 GiB, pinned image (Debian slim, Python 3.12,
  GCC from Debian, Rust 1.99.1), binaries built inside the image (`-O3 -DNDEBUG`,
  `cargo --release`). All implementations are single-threaded.
- Per workload: 2 warm-up runs per implementation (discarded), then 7 measured runs per
  implementation in **randomised order** (seeded shuffle of (implementation, repetition) pairs)
  so that drift during the run affects every implementation alike.
- Identical input files and limits for all implementations.

## 4. Metrics

| Metric | Source | Note |
|---|---|---|
| `wall_ms` | parent `perf_counter_ns` around the child | end-to-end, **includes interpreter start-up** |
| `parse_ms`, `validate_ms`, `search_ms`, `write_ms`, `total_ms` | the implementation's `--timings` | monotonic clock inside the process |
| `peak_rss_mb` | `/usr/bin/time` wrapper (GNU `%M` / BSD `-l`) | whole process, including the Python interpreter. The wrapper prevents fork-inherited RSS (D-020); the floor (`true`) and interpreter baselines are recorded in `metadata.json` |
| `canonicalize_ms` | `--timings` | canonical ordering only (spec v1.1) |
| `search_states`, cut counters | `summary.tsv` | identical across implementations by construction |
| throughput | `search_states / search_ms` | states per second |

Statistics: median and interquartile range across the 7 measured runs (`analysis/analysis.R`).
No result is extrapolated beyond the measured workloads.

## 5. Threats to validity

- Modal's `cpu=1.0` is a reservation, not exclusive core pinning; neighbouring load can add noise.
  Randomised order and IQR reporting make this visible rather than remove it.
- Python start-up dominates `wall_ms` on small workloads; use `search_ms` for algorithmic
  comparisons.
- The three implementations were written by an AI agent against one specification; they are
  idiomatic but not hand-tuned. A different author could produce different relative numbers.
- Synthetic workloads only.
