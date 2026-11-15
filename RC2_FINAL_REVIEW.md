# ColorFrame v1.0.1-rc2 — Final Review

Branch `remediation/v1.0.1-rc2` (from rc1 `44fbbf3`; `main`, `v1.0.0` and rc1 unchanged; no
history rewritten; nothing pushed). Authoritative data unchanged: Modal run `20261115T065950Z`
(commit `cb50ddc`, clean tree; metadata verified). Plan, log and status: `RC2_REMEDIATION_*.md`.

## 1. Summary of corrections

| Finding | Correction | Status |
|---|---|---|
| P0 RQ1 "240/240" | "In all 240 workload-policy runs, every planted ORF meeting the policy-specific true-sample support criterion was recovered. In noisy conditions, additional candidates could also be retained through non-true colour evidence." Raw `recovered == true_ceiling` in 182/240 (all 120 clean; noisy strict 48/60, noisy permissive 14/60) is stated alongside. | PASS |
| P0 support terminology | `spurious_local_only` = local support on every node but ≥ 1 node lacks true-sample support; `recovered_via_spurious_only` = recovered without meeting the policy's true-support criterion. The lead's prescribed permissive and strict sentences are used in the report. Column names kept for schema stability. | PASS |
| P0 "path-coherent" | replaced by "same-sample support across all nodes"; the non-contiguity caveat stays (`LIMITATIONS.md` 11a). | PASS |
| P0 table units | "mean candidates per replicate (clean)"; 100 planted ORFs per replicate stated. | PASS |
| P1 GCC 14 | typed `std::pair<const char*, const std::string*>` array; `-Werror` and all warning flags unchanged. | PASS |
| P1 RSS test | baseline-relative parent-ballast isolation; separate tiny-process, baseline, allocation and exit tests. | PASS |
| P1 stale docs | task board, architecture, reproducibility, TIPE status. | PASS |
| P1 billing | account-level amounts removed; checker rejects them. | PASS |
| P1 authorship | statement and options documented; decision is Ali's (D-025). | DEFERRED |
| P2 internal patch | excluded from archives by `export-ignore`. | PASS |

## 2. Files changed

`README.md`, `reports/TECHNICAL_REPORT.md`, `REMEDIATION_REPORT.md`, `REMEDIATION_STATUS.md`,
`benchmarks/evaluate_rq1.py` (docstring only), `analysis/analysis.R` (panel title only),
`cpp/src/main.cpp`, `tests/test_rq1_model.py`, `tests/test_rss_measurement.py`,
`tests/check_release_archive.py`, `Makefile`, `.gitattributes`, `TASK_BOARD.md`,
`ARCHITECTURE.md`, `REPRODUCIBILITY.md`, `LITERATURE_REVIEW.md`, `TOKEN_ACCOUNTING.md`,
`DECISION_LOG.md` (D-023 wording, D-025), `AI_USAGE.md`, `CHANGELOG.md`; new:
`tests/test_cli_required_flags.py`, `tests/modal_gcc14_build.py`, `tests/modal_rss_check.py`,
`RC2_*.md`.

## 3. Commits

`4c2ab64` plan · `31bd120` RQ1 semantics tests · `2e69e64` RQ1 wording · `4a2459a` GCC 14 tests
(RED) · `5061844` C++ fix (GREEN) · `aed16f9` RSS tests · `2085808` Linux RSS check ·
`9696589` doc reconciliation · `ed6fe51` billing removal · `261a965` authorship ·
`501db83` archive checker (RED) · `07ff020` export-ignore (GREEN) · `efd0966` Makefile ·
plus the commit adding this review.

## 4. Tests added

- `tests/test_rq1_model.py`: 2 semantics tests (14 total).
- `tests/test_cli_required_flags.py`: 5 missing-flag checks + 1 positive check × 3 implementations.
- `tests/test_rss_measurement.py`: rewritten, 5 tests.
- `tests/modal_gcc14_build.py`, `tests/modal_rss_check.py`: environment checks on Modal.
- `tests/check_release_archive.py`: internal patches, temp files, billing details.

## 5. Test results

| Suite | Local macOS (Apple clang 21.0.0, Python 3.15.2, Cargo 1.99.1) | Modal Linux |
|---|---|---|
| `make test` (all suites below + clippy/fmt) | PASS, exit 0 | — |
| Fixture consistency | PASS 39/39 | — |
| Python unit | PASS 45/45 | — |
| C++ unit | PASS 175/175 | PASS 175/175 (GCC 14.4.0) |
| Rust unit | PASS 43/43 | — |
| Conformance | PASS 39/39 × 3 | PASS 39/39 C++ (GCC 14.4.0) |
| Timing contract | PASS × 3 | — |
| RQ1 model | PASS 14/14 | — |
| RSS measurement | PASS 5/5 | PASS 5/5 (Python 3.12.10, GNU time) |
| RSS mutation control | — (macOS does not inherit RSS) | PASS: mutant fails isolation (+300 MB) |
| Required-flag CLI | PASS × 3 | PASS C++ (GCC 14.4.0) |
| Cross-language | PASS 134/134 | rc1 record 134/134 (no algorithm change) |
| Benchmarks | NOT RUN (by design) | NOT RUN: `20261115T065950Z` stands |
| R analysis | NOT RUN (no local R; no analysis change) | NOT RUN |
| GitHub CI | NOT RUN (no remote) | — |

## 6. GCC 14 result

RED before the fix: GCC 14.4.0 (official `gcc:14` image), unchanged `CXXFLAGS = -std=c++17 -O3
-DNDEBUG -Wall -Wextra -Wpedantic -Werror`: `src/main.cpp:76:62: error: possibly dangling
reference to a temporary [-Werror=dangling-reference]`. GREEN after: build, 175/175 unit checks,
39/39 cases and the CLI checks pass. No warning suppression was added.

## 7. RSS portability result

The Python ceiling is gone. Isolation is asserted relative to the same child's pre-ballast
baseline: tolerance 75 MB = 25% of a touched 300 MB parent ballast; inheritance would add
≥ 300 MB. Measured on Modal with the v1.0.0 direct-fork method: `true` 25.3 → 325.3 MB (fails, as
required). With the wrapper: passes on macOS and Modal. **Limitation:** not run on a Python with a
~93 MB baseline like the audit's; the design does not depend on the absolute baseline.
`test_true_is_small` keeps a generous 20 MB bound for a native no-op.

## 8. RQ1 wording corrections

README, technical report (definitions block, column labels, three result bullets), remediation
report, evaluator docstring, R panel title (the existing figure keeps its old title; the report
explains it). Numbers unchanged; no evaluation code changed, so RQ1 was not rerun.

## 9. Documentation reconciliation

Task board (run `20261115T065950Z`, ggCaller verified, TIPE partial); architecture (canonicalize
stage, contract test); reproducibility (spec v1.1; local vs Modal table); TIPE labelled
"Partial review — metadata verified; full-text methodological assessment not completed";
token accounting (no account billing); AI usage (contribution statement, authorship options).

## 10. Release archive verification

Built with `git archive` from the commit containing this review, prefix
`ColorFrame-v1.0.1-rc2/`, checked by `tests/check_release_archive.py`. Its SHA-256 and check
result are reported with the handoff, since a file cannot record its own archive's hash. The
pre-release check of the preceding commit (`efd0966`) passed with 0 problems; `private/` is
untracked and cannot enter a `git archive`.

## 11. Remaining limitations

- Authorship policy (D-025) and attribution reconciliation (D-022): Ali's decision.
- rc2 commits carry `Co-Authored-By` trailers, contrary to D-001 (disclosed; not rewritten).
- `LICENSE`, `CITATION.cff`: not created.
- No GitHub CI run; graph-ID permutation sensitivity untested; TIPE content unread.
- RQ1 figure panel title predates rc2 wording (explained in the report).
- Modal token rotation (`SECURITY.md`) remains an owner action.

## 12. Recommendation

**Ready for the lead's review as v1.0.1-rc2.** Every audit finding within scope is fixed and
verified, except the authorship policy, which is Ali's decision. Before calling it final:
decide D-025 and D-022, choose a licence, and (if publishing) run CI on a private remote.
