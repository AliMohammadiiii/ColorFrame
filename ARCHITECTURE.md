# Architecture

**Status:** Validated for v1; component status in `TASK_BOARD.md`.

(`DESIGN.md` from the original layout is folded into this file — see D-009.)

## 1. Components

```text
                 fixtures/cases/*           generated/* (seed 42)
                 (hand-derived truth)       benchmarks/generate_workloads.py
                        │                            │
                        ▼                            ▼
   ┌──────────────── shared TSV contract (INPUT_OUTPUT_SCHEMA.md) ───────────────┐
   │   python/colorframe.py      cpp/build/colorframe      rust/.../colorframe   │
   │   (reference, stdlib)       (C++17, -O3)              (stable Rust, release)│
   └──────────────┬──────────────────────┬──────────────────────┬────────────────┘
                  ▼                      ▼                      ▼
        candidates.tsv + summary.tsv (+ timings.tsv)   ── byte-compared ──┐
                                                                         ▼
   tests/run_cases.py (conformance)   tests/cross_language.py (generated workloads)
                                                                         │
                         benchmarks/run_benchmarks.py  ◄─────────────────┘
                         benchmarks/modal_app.py (Modal, pinned image)
                                     │
                    results/benchmarks/*.tsv  +  results/agent_usage.csv
                                     │
                       analysis/analysis.R (run on Modal: Debian r-base-core)
                                     │
                        reports/figures/*, reports/TECHNICAL_REPORT.md
```

## 2. Shared contract

Every implementation is a standalone CLI with identical flags, identical output schema and
identical error codes. Equivalence is **byte identity** of `candidates.tsv` and `summary.tsv`.
This makes the comparison independent of language-specific test frameworks and turns every
discrepancy into a concrete diff.

## 3. Internal structure (all three languages)

| Stage | Responsibility | Timed as |
|---|---|---|
| parse | read TSV, check shape, build records | `parse` |
| validate | identifier/DNA/colour/overlap rules, build per-graph adjacency (sorted) | `validate` |
| search | recursive DFS per `ALGORITHM_SPEC.md` §4.2, per graph and policy | `search` |
| write | canonical sort, emit TSV | `write` |

Data representation (common shape, language-idiomatic types):

- node index `0..n-1` in **sorted id order**, so "sorted by id" is "ascending index";
- `seq: bytes`, `colors: sorted int vector`, `succ: index list sorted by target id`;
- search state: walk stack of indices, visit-count array, a byte buffer for `seq` that is
  truncated on backtrack (no per-step string copies), colour intersection saved per frame.

## 4. Repository layout

```text
ColorFrame/
├── *.md, references.bib          documentation (see PROJECT_CHARTER.md §6)
├── python/colorframe.py          reference implementation (stdlib only) + python/tests/
├── cpp/                          C++17 implementation, Makefile, cpp/tests/
├── rust/                         Cargo crate (no dependencies), unit tests in-crate
├── fixtures/cases/               hand-derived conformance cases + FIXTURES.md
├── tests/                        run_cases.py, check_fixtures.py, oracle, cross_language.py
├── benchmarks/                   workload generator, local runner, Modal app
├── generated/                    generated workloads (gitignored, reproducible)
├── analysis/                     R analysis scripts
├── results/                      modal/<run> (timing authority), local/<run> (memory), agent_usage.csv
├── reports/                      technical report and figures
└── .github/workflows/ci.yml      lightweight CI
```

## 5. Key design decisions (details in `DECISION_LOG.md`)

- Uniform overlap per graph and start-position ownership (D-002, D-003) give every ORF exactly
  one canonical record.
- Fully specified exploration order makes even state-limited runs comparable (D-004).
- Recursive DFS is acceptable because depth ≤ `max_path_nodes` (D-005).
- Outputs carry explicit counters for every pruning and every truncation (D-006).
- Hand-derived fixtures + an independent brute-force oracle (D-007).
- Python generator is the single source of benchmark workloads (D-010).
