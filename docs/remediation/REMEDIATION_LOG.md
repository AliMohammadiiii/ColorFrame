# v1.0.1 Remediation Log (chronological, branch `remediation/v1.0.1`)

| Commit | What |
|---|---|
| 3aa59a0 | preserve the lead's uncommitted `AI_USAGE.md` edit (also saved as a patch) |
| c74ce82 | RED: timing-phase contract, policy-order and emission-order tests (all three languages failed as intended) |
| fa26e84 | GREEN: separate canonicalize phase; strict then permissive everywhere (outputs byte-identical to v1.0.0) |
| 0223407, 100ce69 | RED: peak-RSS independence test; macOS portability fix of the test |
| 2d0c73f | GREEN: `/usr/bin/time` wrapper, measurement baselines, canonicalize column in the runner |
| 00d7d3a, 715e12b | spec/schema v1.1; timing contract in `make test` |
| f1e5cfc | RED: 12 RQ1 model and evaluation tests |
| f0b23bc, 945a53c, 456e027 | GREEN: paired RQ1 generator with explicit noise, true-sample evaluator, benchmark flag, `make test` |
| 941fe5f, cb50ddc | R replicate statistics; GNU time and in-container test suites on Modal |
| 46ae72d, 555d9bf | verified references; ggCaller prior art from full text |
| (attribution, ledger, spec) | reconciled `AI_USAGE.md`; remediation usage NOT_EXPOSED; explicit complexity and representation sections |
| e08720b, 37f7e1d | authoritative v1.0.1 run `20261115T065950Z`; v1.0.0 results marked superseded and archived |
| (docs) | README, technical report, release check, remediation documents |

Environment events: the disk filled (ENOSPC) mid-implementation and was freed by the lead. Two
Modal probe runs (scratch code, not in the repo) established that the sandbox lacks `VmHWM` and
that child `ru_maxrss` inherits the harness's RSS through fork. Elicit and Scite were unavailable.
