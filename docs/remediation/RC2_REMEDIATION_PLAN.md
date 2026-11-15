# v1.0.1-rc2 Remediation Plan

Input: the independent audit of `ColorFrame-v1.0.1-rc-44fbbf3.zip` (kept in `private/`, not
distributed) and the lead's rc2 mission. Branch `remediation/v1.0.1-rc2` from `44fbbf3`
(rc1, preserved). Scope: precision, portability and release hygiene only — no algorithm,
experiment or benchmark changes. Status: `RC2_REMEDIATION_STATUS.md`; log: `RC2_REMEDIATION_LOG.md`.

Each finding was verified against the source before planning:

| # | Pri | Finding | Verified | Correction | Tests |
|---|---|---|---|---|---|
| F1 | P0 | "recover exactly their ceilings (240/240)" | yes: within-ceiling 240/240, raw `recovered == true_ceiling` 182/240 (noisy strict 48/60, noisy permissive 14/60) | precise wording everywhere | – (wording) |
| F2 | P0 | `spurious_local_only` / `recovered_via_spurious_only` read as "only noise" | yes: `all_local AND NOT true_local`; evaluator docstring said "exists only via noise" | exact definitions in evaluator, report, README; column names kept (schema stable) | semantics test: mixed true/non-true nodes |
| F3 | P0 | "path-coherent support" | yes: README, report, remediation report | "same-sample support across all nodes" | – |
| F4 | P0 | candidate columns are replicate means | yes | relabel | – |
| F5 | P1 | GCC 14 `-Wdangling-reference` with `-Werror` (`cpp/src/main.cpp:74`) | no GCC 14 locally; verified on Modal (`gcc:14` image) | explicitly typed local array | strict-warning build check + CLI missing-flag tests |
| F6 | P1 | fixed 60 MB Python RSS threshold | yes (`tests/test_rss_measurement.py`) | baseline-relative parent-ballast isolation | 4 separate tests |
| F7 | P1 | stale docs | yes: TASK_BOARD run id and ggCaller status, ARCHITECTURE write stage, REPRODUCIBILITY spec v1.0 and local/Modal split, TIPE status | reconcile | – |
| F8 | P1 | account-level billing amount in `TOKEN_ACCOUNTING.md` | yes (also a non-numeric mention in D-023) | remove; keep project-level statement | archive checker rejects billing amounts |
| F9 | P1 | Git authorship policy | yes (D-001) | decide and document a policy for future commits (pending the lead) | – |
| F10 | P1 | internal patch in external archive | yes (`archive/remediation/`) | exclude via `.gitattributes export-ignore` | checker rejects `archive/remediation/` |

Benchmarks are **not** rerun: no search, timing, data-structure or benchmark-execution code
changes. The C++ CLI change touches argument checking only; it is verified by the full C++
test suite and cross-language equivalence.
