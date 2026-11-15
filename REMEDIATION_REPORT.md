# ColorFrame v1.0.1 — Remediation Report

Branch `remediation/v1.0.1` (from `v1.0.0` = `3a02403`; history preserved). Authoritative rerun:
`results/modal/20261115T065950Z` (commit `cb50ddc`, clean). Plan, status and log:
`REMEDIATION_PLAN.md`, `REMEDIATION_STATUS.md`, `REMEDIATION_LOG.md`.

## 1. What was wrong, why it mattered, what changed

| Finding | Why it mattered | Change | Tests added |
|---|---|---|---|
| **A. Timing phases unequal.** C++ and Rust sorted candidates inside `search`; Python did not. Rust ran permissive first. | v1.0.0 search speed-ups compared different work. | Spec v1.1: six contiguous phases; sorting moved to `canonicalize`; strict then permissive everywhere. Outputs byte-identical to v1.0.0. | shared timing contract; per-language order and emission-order tests |
| **Modal RSS floor.** v1.0.0 blamed the sandbox (D-015). The real cause: on Linux a child's `ru_maxrss` inherits the harness's RSS through fork. | All Modal memory values below ~51 MB were artefacts. | `/usr/bin/time` wrapper; floor and interpreter baselines recorded per run. | `test_rss_measurement.py` (passes on macOS and in the Modal container) |
| **B. RQ1 counted spurious colours as evidence.** | Permissive recovery was overstated. | Explicit `p_true_observation` and `p_spurious_colour`; clean and noisy conditions; true-sample metrics; policy-specific ceilings. | 12 tests: five support cases, ceilings, determinism, pairing, clean = only true samples, noisy adds only non-true samples, end-to-end ceilings |
| **C. One realisation per p.** | No sense of variability. | 10 paired replicates with common random numbers; replicate statistics in R. | determinism and pairing tests |
| **D. ZIP leaked private material.** | Privacy. | `git archive` from the release commit plus `tests/check_release_archive.py`. | archive check |
| **E. Prior art.** | Overstated novelty risk. | ggCaller read in full; all references verified at primary sources. | – |
| **F/G. Token framing, attribution.** | Unsupported inference; unclear credit. | RQ4 is descriptive; attribution reconciled (pending the lead). | – |

## 2. Experiments rerun

All 134 workloads (perf and stress inputs byte-identical to v1.0.0; 120 new paired RQ1
workloads), conformance and equivalence, then the full benchmark (2 warm-up + 7 measured, random
order) and R analysis, on Modal in one pinned container. Container wall time 179.5 s.

## 3. What the corrected results show

- **RQ1:** both policies recover exactly their true-support ceilings (240/240). At p = 0.3, strict
  sees 10.1 [7.6, 12.6] and permissive 43.6 [40.7, 46.5] of 100 planted ORFs, at 3.5× the
  candidate volume. With spurious colours, permissive retains up to 10.9 ORFs that lack true
  support; strict at most 0.5. The previous claim that permissive recovers 63% at p = 0.3 is
  withdrawn: 11 of those 63 were due to noise, and the design has changed.
- **RQ2:** corrected search-phase speed-ups are *larger* than v1.0.0's (C++ 16–30×, Rust 17–42×
  on graph workloads; 92–108× on stress), because the old compiled "search" included sorting.
  In-process totals are 3.7–12.4× on the perf graphs.
- **Memory (Linux):** real values now, e.g. stress Python 16.6 / C++ 6.7 / Rust 4.7 MB.

## 4. Claims now justified

- The three implementations are behaviourally identical on all 39 cases and 134 workloads, and
  their timing phases cover equivalent work.
- On these synthetic workloads, on this hardware, these implementations rank Rust > C++ ≫ Python
  for the search phase.
- In this synthetic model, path-coherent (strict) support is rarer but robust to spurious
  colours; local (permissive) support recovers more but admits noise-enabled candidates.

## 5. Claims that must not be made

- That ColorFrame finds or validates genes, or is a new gene-calling method.
- That colour support shows a walk exists in any one cell.
- Any general statement about Python, C++ or Rust, or about genome-scale performance.
- Any relationship between AI token use and quality or performance.
- Any v1.0.0 search speed-up or Modal memory figure.

## 6. Unresolved

- **Attribution:** pending the lead's confirmation (D-022).
- **`LICENSE` / `CITATION.cff`:** not created. The licence choice and author metadata are the
  lead's decision.
- **GitHub CI:** not run (no remote; publishing needs approval).
- **Graph-ID permutation sensitivity:** not tested (limitation).
- **TIPE (Kalatzis 2026):** metadata verified, content unread.
- **Elicit / Scite:** unavailable in this session.
- **Token usage:** v1.0.1 Opus usage is `NOT_EXPOSED`.
- **Branch status:** not merged to `main`, not tagged; awaiting review.

## 7. Release archive

Built with `git archive` from the release-candidate commit and checked by
`tests/check_release_archive.py`. The SHA-256 and result are reported to the lead with the
release candidate. Private files are untracked and so cannot enter a `git archive`.
