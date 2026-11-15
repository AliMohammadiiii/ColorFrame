# Task Board

Status labels: Planned · In progress · Implemented · Tested · Validated · Deferred.
Every item is accountable to Ali (project lead). Agent attribution: `AI_USAGE.md`.

| ID | Task | Branch | Owner | Status |
|---|---|---|---|---|
| T00 | Repository, `.gitignore`, `SECURITY.md` | main | Opus | Validated |
| T01 | Charter, architecture, algorithm spec, I/O schema, decision log | docs/project-architecture | Opus | Validated |
| T02 | 39 hand-derived fixtures, oracle, conformance runner | test/colorframe-fixtures, fix/fixture-counters | Opus | Validated (oracle + 3 implementations) |
| T03 | Python reference implementation (TDD) | feat/python-implementation | Sonnet | Validated (42 unit, 39/39, cross-language) |
| T04 | C++17 implementation (TDD) | feat/cpp-implementation | Sonnet | Validated (165 checks, 39/39, cross-language) |
| T05 | Rust implementation (TDD) | feat/rust-implementation | Sonnet | Validated (41 unit, clippy/fmt, 39/39, cross-language) |
| T06 | Workload generator + cross-language validation | feat/cross-language-validation | Opus | Validated (20/20 byte-identical) |
| T07 | Benchmark runner, Modal app | feat/cross-language-validation, fix/modal-* | Opus | Validated (authoritative run **20261115T065950Z**, v1.0.1; 20261114T181422Z superseded) |
| T08 | Token accounting ledger | feat/token-accounting, fix/usage-ledger-csv | Opus | Implemented (telemetry partly NOT_EXPOSED) |
| T09 | R analysis | (in feat/token-accounting commit), fix/rq1-limits-and-memory | Opus | Validated (ran on Modal, R 4.2.2) |
| T10 | Literature metadata verification | docs/literature-review | Haiku, Opus | Validated: metadata at primary sources; ggCaller workflow verified from the full text (v1.0.1); TIPE partial (metadata only) |
| T11 | CI workflow + Makefile | feat/ci, fix/ci-cross-workloads | Haiku, Opus | Tested locally (`make test`); not run on GitHub (no remote) |
| T12 | Final report, limitations, reproducibility | docs/final-report | Opus | Validated |
| — | Reverse strand, partial genes, candidate scoring | — | — | Deferred (out of v1 scope) |
| — | Publish to a public remote | — | Ali | Planned (requires lead's permission) |
| — | Rotate the Modal token pasted in chat | — | Ali | Planned (owner action, see SECURITY.md) |
| R1–R9 | v1.0.1 remediation | remediation/v1.0.1 | Opus | see `REMEDIATION_STATUS.md` |
| F1–F10 | v1.0.1-rc2 precision pass | remediation/v1.0.1-rc2 | Opus | see `RC2_REMEDIATION_STATUS.md` |
