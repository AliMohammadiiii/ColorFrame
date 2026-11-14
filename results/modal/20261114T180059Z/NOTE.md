# Superseded run

First complete Modal run (commit 3eeea97, clean tree). Kept for transparency; **not used in the report**.

- `rq1_recovery.tsv`: `perf_n10000_*` rows were evaluated with the default 50 000-state limit instead of the workload limit (bug fixed in f682857). `rq1_*` rows are unaffected.
- `peak_rss_mb`: the Modal sandbox reports a floor of 51.95 MB for child processes, so values below it are not measurable (see D-015).
- Timings and correctness checks in this run are valid (all checks passed in-container).
