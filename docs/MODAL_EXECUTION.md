# Modal Execution

**Status:** Implemented and executed (Modal client 1.6.3).

## Authentication (never commit credentials)

```bash
modal token set --profile <name>      # interactive; writes ~/.modal.toml outside the repo
modal profile activate <name>
modal profile current                 # prints the profile name only
```

See `SECURITY.md`. The app reads no secrets and writes none.

## Running

```bash
modal run benchmarks/modal_app.py                                  # full pipeline + R analysis
modal run benchmarks/modal_app.py --reps 7 --warmup 2
modal run benchmarks/modal_app.py --stage analysis --run-id <ID>   # re-run R on stored results
modal run benchmarks/modal_app.py --stage analysis --results-dir results/local/<ID>
modal run --detach benchmarks/modal_app.py                         # robust to a dropped client
modal volume get colorframe-results <run_id>.tar.gz .              # fetch results after a disconnect
```

Use `--detach` on unstable connections: a dropped client stopped one run (D-016). The pipeline
also writes its results to the `colorframe-results` Volume.

Results go to `results/modal/<UTC run id>/`; figures and tables to `reports/figures/`.

## What runs where

| Function | Image | Resources | Steps |
|---|---|---|---|
| `pipeline` | `debian_slim` + Python 3.12 + `build-essential` + rustup 1.99.1 (minimal, rustfmt, clippy); repo copied in; C++ and Rust built at image build time | `cpu=1.0`, 4096 MiB, timeout 4 h | `check_fixtures` → `run_cases --impl all` → generate workloads → `cross_language` → `evaluate_rq1` → `run_benchmarks` |
| `analysis` | `debian_slim` + Python 3.12 + Debian `r-base-core` | `cpu=1.0`, 2048 MiB | `Rscript analysis/analysis.R` (base R only) |

The image copies the repository with `.git`, `.worktrees`, `private`, `generated`, `results`,
`reports` and build directories excluded. The commit hash and a dirty-tree flag are passed into
the container as environment variables and recorded in `pipeline.log` and `metadata.json`.

## Recorded per run

`metadata.json` (commit, dirty flag, Python/GCC/rustc versions, binary SHA-256, workload
parameters and input SHA-256, reps/warm-up/order seed), `pipeline.log` (every command and its
output), `cpuinfo.txt`, `meminfo.txt`, `raw_runs.tsv`, `cross_language.tsv`,
`rq1_recovery.tsv`, `r_version.txt`.

**Environment notes:** `/proc/cpuinfo` reports `model name: unknown`; `/proc/<pid>/status` has no `VmHWM` (gVisor). Peak RSS is measured through GNU `time` (installed in the image), which avoids fork-inherited RSS (D-020). Each run also records `modal_env.txt` (non-secret `MODAL_*` identifiers such as the image and task ids) and the CPU/memory allocation.

## Cost

Modal compute cost is tracked separately from model-API cost. The pipeline log records the
container's wall time (`container_wall_seconds`). The billed amount is visible only in the
Modal dashboard and is recorded in `TOKEN_ACCOUNTING.md` as `NOT_EXPOSED` unless entered by the
project lead.
