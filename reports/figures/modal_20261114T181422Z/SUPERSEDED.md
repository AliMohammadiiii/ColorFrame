# Superseded (v1.0.0 protocol)

Kept unchanged for the historical record; **superseded by `results/modal/20261115T065950Z`** (v1.0.1).

Why (see `REMEDIATION_REPORT.md`):

- `search_ms` was not phase-equivalent: C++ and Rust sorted candidates inside the search timer, Python did not (D-019). Search speed-ups from this run must not be quoted.
- Rust executed permissive before strict; the others strict before permissive.
- On Linux (Modal), peak RSS inherited the benchmark harness memory through fork (~51 MB floor, D-020). macOS values were not affected by that floor but used the old phase boundaries.
- RQ1 used one realisation per p and counted spurious colours as evidence (D-021).

`total_ms` and `wall_ms` covered equivalent work in all implementations and remain usable as historical in-process and end-to-end measurements of that protocol.
