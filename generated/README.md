# generated/

Benchmark workloads are **not committed**. They are fully reproducible:

```bash
python3 benchmarks/generate_workloads.py            # all workloads
python3 benchmarks/generate_workloads.py rq1_p50    # just one
```

Each workload directory contains `nodes.tsv`, `edges.tsv`, `planted.tsv` (known planted ORFs)
and `params.json` (seed, parameters, realised statistics, CLI arguments). Input SHA-256 checksums
of the benchmarked files are recorded in `results/modal/<run>/metadata.json`.
