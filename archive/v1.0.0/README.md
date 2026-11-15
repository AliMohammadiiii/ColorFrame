# ColorFrame

**Frame-aware candidate path search in coloured sequence graphs: algorithmic trade-offs and
cross-language performance.**

Project lead: Ali Mohammadi · Status: **v1.0.0, validated** · Engineering by AI development
agents under the lead's direction (see `AI_USAGE.md`).

ColorFrame enumerates forward-strand ORFs (`ATG` … first in-frame stop) along walks of a small
coloured sequence graph. It tracks the reading frame across node boundaries, overlaps, branches,
loops and repeats, and applies one of two sample-evidence policies (**strict**: one sample must
cover every node; **permissive**: every node must be seen in some sample). Every search bound
that truncates the search is reported. The same algorithm is implemented in **Python, C++17 and
Rust**, and all three produce byte-identical output.

It is a deliberately simplified research prototype, **not** a gene caller (see `LIMITATIONS.md`).

## Results at a glance (`reports/TECHNICAL_REPORT.md`)

- **RQ1:** each policy recovers exactly the planted ORFs its evidence rule allows. With 30%
  per-cell observation probability, strict recovers 18% and permissive 63% of planted ORFs.
  Permissive emits 3.3× more candidates, 69% of them without a shared sample.
- **RQ2:** median search time vs Python: C++ 15–28× and Rust 17–39× faster on graph workloads;
  83× and 103× on the stress workload. Rust beats C++ on 19 of 20 workloads (Linux/GCC).
- **RQ3:** time is linear in graph size and in the state limit; memory is dominated by stored
  candidates (compiled) or the interpreter baseline (Python).
- **RQ4:** the recorded AI tokens per implementation differ by about 15% (incomplete telemetry);
  no effort–performance relationship can be claimed.

## Quick start

```bash
make test                                  # fixtures, unit tests, lint, 39 conformance cases × 3, cross-language
python3 python/colorframe.py --nodes fixtures/cases/G11_frame_shifting_loop/nodes.tsv \
  --edges fixtures/cases/G11_frame_shifting_loop/edges.tsv --policy both \
  --out candidates.tsv --summary summary.tsv
modal run --detach benchmarks/modal_app.py # authoritative benchmark + R analysis
```

## Where things are

| Start here | |
|---|---|
| `PROJECT_CHARTER.md` | roles, research questions, scope |
| `ALGORITHM_SPEC.md` | the algorithm (normative) |
| `fixtures/FIXTURES.md` | hand-derived ground truth, with worked examples |
| `reports/TECHNICAL_REPORT.md` | results and discussion |
| `DECISION_LOG.md` | every non-obvious decision, including corrections |
| `AI_USAGE.md`, `TOKEN_ACCOUNTING.md` | who did what, and what it cost |

Other documents: `ARCHITECTURE.md`, `INPUT_OUTPUT_SCHEMA.md`, `TEST_PLAN.md`,
`BENCHMARK_PROTOCOL.md`, `MODAL_EXECUTION.md`, `REPRODUCIBILITY.md`, `LITERATURE_REVIEW.md`,
`PRIOR_ART_AND_SCOPE.md`, `LIMITATIONS.md`, `SECURITY.md`, `TASK_BOARD.md`, `CHANGELOG.md`.
