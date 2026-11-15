# Reproducibility

**Status:** Validated for v1.0.1-rc2. Where each check actually ran is listed below; the
authoritative benchmark and RQ1 results come only from Modal.

## Where validation ran (v1.0.1 / rc2)

| Check | Local macOS (Apple clang, Python 3.15, Rust 1.99.1) | Modal Linux |
|---|---|---|
| `make test` (fixtures, 3× unit tests, clippy/fmt, timing contract, RQ1 model, RSS, 39 cases × 3, 134-workload equivalence) | run, PASS (rc2 final run: `RC2_FINAL_REVIEW.md`) | the same suites inside the benchmark container of run `20261115T065950Z` (Debian, Python 3.12.10, GCC 12.2.0, Rust 1.99.1) |
| Authoritative benchmark (420 measured rows), RQ1 evaluation (240 rows), R analysis (R 4.2.2) | not authoritative; local timings informative only | run `20261115T065950Z`, commit `cb50ddc`, clean tree |
| GCC 14 `-Werror` build, C++ unit checks, 39 cases, CLI required flags | not available (no GCC 14 locally) | `tests/modal_gcc14_build.py`, official `gcc:14` image, GCC 14.4.0 |
| RSS measurement tests, incl. direct-fork mutation control | tests run (macOS BSD `time`) | `tests/modal_rss_check.py` (Debian, Python 3.12.10, GNU time) |
| R analysis | not run (no local R) | yes |

rc2 changed no search, timing, data-structure or benchmark-execution code, so the benchmark was
not rerun; `20261115T065950Z` remains authoritative.

## Local (no Modal needed)

Requirements: Python ≥ 3.12 (standard library only), a C++17 compiler, rustup (the toolchain
is pinned in `rust/rust-toolchain.toml` and installs automatically).

```bash
make test                                   # fixtures, unit tests (3 languages), clippy/fmt, conformance, cross-language
python3 benchmarks/generate_workloads.py    # deterministic workloads (seed 42) -> generated/
python3 tests/cross_language.py             # byte-identical outputs across python/cpp/rust
python3 benchmarks/evaluate_rq1.py --impl rust --out results/rq1_recovery.tsv
python3 benchmarks/run_benchmarks.py --out results/benchmarks/local --reps 7 --warmup 2
```

Local timings are informative only. Authoritative numbers come from Modal.

## Authoritative run (Modal)

```bash
modal run benchmarks/modal_app.py           # see MODAL_EXECUTION.md
```

## What makes runs reproducible

| Element | Mechanism |
|---|---|
| Inputs | generator seeded per workload with `"42:<name>"`; SHA-256 of every input in `metadata.json` |
| Algorithm | frozen spec **v1.1** (v1.0 semantics plus fixed policy execution order and separate canonicalize phase, D-019) with fully specified exploration order (D-004) |
| Correctness | 39 hand-derived conformance cases + byte-identity across languages, re-run inside the benchmark container before timing |
| Toolchains | Python 3.12 (Modal image), Debian GCC, Rust 1.99.1 pinned; versions and binary SHA-256 recorded |
| Code version | commit hash and dirty flag recorded in every run |
| Order effects | seeded randomised execution order (`--seed 42`) |
| Analysis | base R only (no package versions to drift), run in a container; R version recorded |

## Known sources of variation

Timing noise on shared cloud CPUs (reported as IQR), and differences in CPU model between Modal
runs (recorded in `cpuinfo.txt`). Results from different runs or machines must not be pooled
without saying so.
