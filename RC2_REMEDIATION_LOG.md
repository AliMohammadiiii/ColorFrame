# v1.0.1-rc2 Remediation Log (branch `remediation/v1.0.1-rc2`, from rc1 `44fbbf3`)

| Commit | What |
|---|---|
| 4c2ab64 | rc2 plan; every audit finding verified against the source first (e.g. raw recovered = criterion count in 182/240) |
| 31bd120 | RQ1 semantics tests: mixed true/non-true nodes; strict passing on a shared non-true colour (pass immediately: they pin definitions, no behaviour change) |
| 2e69e64 | RQ1 wording in README, technical report, remediation report, evaluator docstring, R panel title |
| 4a2459a | RED: required-flag CLI test; Modal GCC 14 check fails with `-Werror=dangling-reference` at `main.cpp:76` (GCC 14.4.0) |
| 5061844 | GREEN: typed local array in the C++ CLI; `-Werror` unchanged; GCC 14.4.0 and Apple clang pass |
| aed16f9 | RSS tests made baseline-relative (no fixed Python ceiling) |
| 2085808 | Modal RSS check with direct-fork mutation control (mutant fails isolation by +300 MB) |
| 9696589 | task board, architecture, reproducibility, TIPE status reconciled |
| ed6fe51 | account-level billing details removed |
| 261a965 | contribution statement; authorship options (D-025, pending) |
| 501db83 | RED: archive checker rejects internal patches, temp files, billing details |
| 07ff020 | GREEN: `export-ignore` for `archive/remediation/` |
| efd0966 | required-flag checks in `make test` |
| (this commit) | rc2 status, log, final review, changelog |

Environment notes: no GCC 14 or R on the Mac, so the GCC 14 check ran on Modal (`gcc:14`).
The audit environment's Python (~93 MB baseline) was not available; portability is shown
through the baseline-relative design and two environments (macOS, Modal Debian).
