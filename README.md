# ColorFrame

**Frame-aware candidate path search in coloured sequence graphs: a controlled algorithmic and
engineering prototype.**

Project lead: Ali Mohammadi · Status: **v1.0.1 release candidate** (remediated after an independent
review; see `REMEDIATION_REPORT.md`) · Engineering by AI development agents under the lead's
direction (`AI_USAGE.md`).

ColorFrame enumerates forward-strand ORFs (`ATG` … first in-frame stop) along walks of a small
coloured sequence graph. It tracks the reading frame across overlaps, branches, loops and
repeats, and applies one of two sample-evidence policies:
- **strict**: one colour must be shared by every node of the walk;
- **permissive**: every node must have some colour.

Every bound that truncates the search is reported. The same algorithm is implemented in Python,
C++17 and Rust, with byte-identical outputs. It is **not** a gene caller. ggCaller already
performs frame-aware DFS ORF discovery on population-wide coloured DBGs, with FM-index path
validation (`PRIOR_ART_AND_SCOPE.md`).

## Results (authoritative run `results/modal/20261115T065950Z`, Modal 1 CPU, Linux/GCC)

- **RQ1, synthetic support-policy trade-off** (10 paired replicates; 100 planted ORFs each).
  In all 240 workload-policy runs, every planted ORF meeting the policy-specific true-sample support criterion was recovered. In noisy conditions, additional candidates could also be retained through non-true colour evidence (raw recovered count = criterion count in 182/240 runs; all 58 exceptions are noisy).
  Clean, p_true_observation = 0.3: 10.1 planted ORFs (95% CI 7.6–12.6) have a true sample shared
  by all their nodes (strict criterion), and 43.6 (40.7–46.5) have true-sample support on every
  node (permissive criterion); permissive outputs 3.5× more candidates. Noisy
  (`p_spurious = 0.25·p`): permissive also retains up to 10.9 planted paths (replicate mean) in
  which **at least one node lacks true-sample support**; strict retains ≤ 0.5 paths whose only
  all-node shared colour is non-true. None of this is gene validation.
- **RQ2/RQ3, these three implementations:** search phase vs Python, C++ 16–30× and Rust 17–42×
  faster on graph workloads, 92–108× on the stress workload; all in-process phases (`total_ms`),
  C++ 3.7–9.5× and Rust 8.6–12.4× on the perf graphs. Rust's search beats C++ on 19 of 20
  workloads. Linux peak RSS (wrapper floor 2.9 MB, Python interpreter 13.9 MB): stress C++
  6.7 MB, Rust 4.7 MB, Python 16.6 MB.
- **AI-assisted development:** a descriptive process trace with incomplete telemetry
  (`TOKEN_ACCOUNTING.md`). No effort–performance claim.

v1.0.0 search speed-ups and Modal memory figures were **invalid** (unequal timing phases; RSS
inherited from the harness) and are superseded (`archive/v1.0.0/`).

## Quick start

```bash
make test                                   # fixtures, unit tests, lint, timing/RQ1/RSS contracts, 39 cases x 3, 134-workload equivalence
modal run --detach benchmarks/modal_app.py  # authoritative benchmark + RQ1 + R analysis
```

## Documents

`reports/TECHNICAL_REPORT.md` (results) · `REMEDIATION_REPORT.md` (what changed and why) ·
`ALGORITHM_SPEC.md` (v1.1) · `INPUT_OUTPUT_SCHEMA.md` · `fixtures/FIXTURES.md` ·
`BENCHMARK_PROTOCOL.md` · `LITERATURE_REVIEW.md` · `PRIOR_ART_AND_SCOPE.md` · `LIMITATIONS.md` ·
`AI_USAGE.md` · `TOKEN_ACCOUNTING.md` · `DECISION_LOG.md` · `REPRODUCIBILITY.md` · `SECURITY.md`.
