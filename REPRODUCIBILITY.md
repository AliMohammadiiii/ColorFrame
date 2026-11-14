# Reproducibility

**Status:** Validated: the full pipeline ran from a clean commit on Modal, and locally on macOS.

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
| Algorithm | frozen spec v1.0 with fully specified exploration order (D-004) |
| Correctness | 39 hand-derived conformance cases + byte-identity across languages, re-run inside the benchmark container before timing |
| Toolchains | Python 3.12 (Modal image), Debian GCC, Rust 1.99.1 pinned; versions and binary SHA-256 recorded |
| Code version | commit hash and dirty flag recorded in every run |
| Order effects | seeded randomised execution order (`--seed 42`) |
| Analysis | base R only (no package versions to drift), run in a container; R version recorded |

## Known sources of variation

Timing noise on shared cloud CPUs (reported as IQR), and differences in CPU model between Modal
runs (recorded in `cpuinfo.txt`). Results from different runs or machines must not be pooled
without saying so.
