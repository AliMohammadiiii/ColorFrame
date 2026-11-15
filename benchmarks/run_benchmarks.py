#!/usr/bin/env python3
"""Benchmark runner (BENCHMARK_PROTOCOL.md). Same code runs locally and inside Modal.

For each workload, every implementation is run `--warmup` times (discarded) and `--reps`
times (measured). The order of (implementation, repetition) pairs within a workload is
shuffled with a seeded RNG so drift affects all implementations alike.

Per measured run we record
  wall_ms      end-to-end wall time around the child process (includes interpreter start-up)
  parse/validate/search/canonicalize/write/total_ms   in-process phase timings (--timings, spec v1.1)
  peak_rss_mb  child's peak resident set size via /usr/bin/time (see measure(); D-020)
plus search counters summed over the summary rows. Correctness: the first run of each
implementation is byte-compared with the others; the workload is marked invalid otherwise.

    python3 benchmarks/run_benchmarks.py --out results/benchmarks/local [--reps 7 --warmup 2]
"""
import argparse
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from run_cases import IMPLS  # noqa: E402

SUMMARY_COUNTERS = ["search_states", "candidates", "color_pruned", "dead_ends", "orf_length_cuts",
                    "path_length_cuts", "node_visit_cuts", "state_limit_hit"]


TIME_BIN = "/usr/bin/time"


def measure(cmd):
    """Run cmd once; return {"wall_ms", "peak_rss_mb", "exit", "stderr"}.

    Peak RSS comes from /usr/bin/time (GNU `-f %M` in KiB on Linux, BSD `-l` in bytes on macOS),
    which forks the measured program itself. Forking it directly from this (large) Python process
    would make its ru_maxrss inherit our RSS on Linux, because the high-water mark survives exec;
    that produced the ~51 MB floor of the v1.0.0 Modal run (D-020). wall_ms includes the wrapper's
    start-up, which is measured separately as a baseline (`true`).
    """
    with tempfile.NamedTemporaryFile(suffix=".rss", delete=False) as fh:
        rss_file = fh.name
    try:
        if sys.platform.startswith("linux"):
            wrapper = [TIME_BIN, "-f", "%M", "-o", rss_file]
        elif sys.platform == "darwin":
            wrapper = [TIME_BIN, "-l", "-o", rss_file]
        else:
            raise RuntimeError(f"peak-RSS measurement not supported on {sys.platform}")
        t0 = time.perf_counter_ns()
        p = subprocess.run(wrapper + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        wall = (time.perf_counter_ns() - t0) / 1e6
        text = Path(rss_file).read_text()
    finally:
        os.unlink(rss_file)
    if sys.platform.startswith("linux"):
        rss = int(text.strip().splitlines()[-1]) / 1024.0                 # KiB -> MiB
    else:
        line = next(l for l in text.splitlines() if "maximum resident set size" in l)
        rss = int(line.split()[0]) / (1024.0 * 1024.0)                     # bytes -> MiB
    return {"wall_ms": wall, "peak_rss_mb": rss, "exit": p.returncode, "stderr": p.stderr.decode()}


def run_once(impl, wdir, args, tmp):
    out, summ, tim = tmp / "c.tsv", tmp / "s.tsv", tmp / "t.tsv"
    cmd = IMPLS[impl] + ["--nodes", str(wdir / "nodes.tsv"), "--edges", str(wdir / "edges.tsv"),
                         "--out", str(out), "--summary", str(summ), "--timings", str(tim)] + args
    m = measure(cmd)
    if m["exit"] != 0:
        raise RuntimeError(f"{impl} on {wdir.name}: exit {m['exit']}: {m['stderr'][:300]}")
    wall = m["wall_ms"]
    phases = dict(line.split("\t") for line in tim.read_text().splitlines()[1:])
    srows = [dict(zip(*[l.split("\t") for l in (summ.read_text().splitlines()[0], r)]))
             for r in summ.read_text().splitlines()[1:]]
    counters = {k: sum(int(r[k]) for r in srows) for k in SUMMARY_COUNTERS}
    digest = hashlib.sha256(out.read_bytes() + summ.read_bytes()).hexdigest()[:16]
    return wall, phases, m["peak_rss_mb"], counters, digest


def tool_version(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.splitlines()[0].strip()
    except Exception as e:  # noqa: BLE001 - metadata only
        return f"unavailable ({type(e).__name__})"


def environment():
    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    commit = tool_version(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": os.environ.get("COLORFRAME_COMMIT", commit),
        "host": platform.node() if os.environ.get("COLORFRAME_ENV") != "modal" else "modal-container",
        "environment": os.environ.get("COLORFRAME_ENV", "local"),
        "cpu_allocation": os.environ.get("COLORFRAME_CPU", "not set (local machine)"),
        "memory_allocation_mb": os.environ.get("COLORFRAME_MEMORY_MB", "not set (local machine)"),
        "rss_method": "/usr/bin/time wrapper (GNU %M KiB on Linux, BSD -l bytes on macOS); see D-020",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count_visible": os.cpu_count(),
        "python": sys.version.split()[0],
        "cxx": tool_version([os.environ.get("CXX", "c++"), "--version"]),
        "rustc": tool_version(["rustc", "--version"]),
        "binaries_sha256": {k: sha(v[-1]) for k, v in IMPLS.items() if Path(v[-1]).exists()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--impls", default="python,cpp,rust")
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--skip", nargs="*", default=[], help="skip (impl:workload) pairs, e.g. python:stress_s800000")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    impls = a.impls.split(",")
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    tmp = outdir / ".tmp"
    tmp.mkdir(exist_ok=True)
    rng = random.Random(a.seed)
    wdirs = sorted(d for d in (ROOT / "generated").iterdir() if (d / "params.json").exists())
    if a.only:
        wdirs = [d for d in wdirs if d.name in a.only]
    skip = set(a.skip)

    meta = environment()
    # Measurement floor and runtime baselines, measured with the same wrapper (median of 7).
    base = {}
    for name, cmd in (("wrapper_floor_true", [shutil.which("true")]), ("python_interpreter", [sys.executable, "-c", "pass"])):
        ms = [measure(cmd) for _ in range(7)]
        base[name] = {"peak_rss_mb_median": sorted(x["peak_rss_mb"] for x in ms)[3],
                      "wall_ms_median": sorted(x["wall_ms"] for x in ms)[3]}
    meta["measurement_baselines"] = base
    meta.update({"reps": a.reps, "warmup": a.warmup, "order_seed": a.seed, "impls": impls, "workloads": {}})
    raw = open(outdir / "raw_runs.tsv", "w")
    raw.write("workload\timpl\trep\torder\twall_ms\tparse_ms\tvalidate_ms\tsearch_ms\tcanonicalize_ms\twrite_ms\ttotal_ms\t"
              "peak_rss_mb\t" + "\t".join(SUMMARY_COUNTERS) + "\toutput_sha256_16\n")
    for w in wdirs:
        params = json.loads((w / "params.json").read_text())
        if not params.get("benchmark", True):     # RQ1 replicates beyond r00/clean are not timed
            continue
        args = params["cli_args"].split()
        meta["workloads"][w.name] = {
            "params": params,
            "nodes_sha256": hashlib.sha256((w / "nodes.tsv").read_bytes()).hexdigest(),
            "edges_sha256": hashlib.sha256((w / "edges.tsv").read_bytes()).hexdigest(),
        }
        active = [i for i in impls if f"{i}:{w.name}" not in skip]
        for i in active:                                   # warm-up, discarded
            for _ in range(a.warmup):
                run_once(i, w, args, tmp)
        jobs = [(i, r) for i in active for r in range(a.reps)]
        rng.shuffle(jobs)
        digests = {}
        for order, (i, r) in enumerate(jobs):
            wall, ph, rss, cnt, dg = run_once(i, w, args, tmp)
            digests.setdefault(i, set()).add(dg)
            raw.write("\t".join(map(str, [w.name, i, r, order, f"{wall:.3f}", ph["parse"], ph["validate"],
                                          ph["search"], ph["canonicalize"], ph["write"], ph["total"], f"{rss:.2f}"]
                                     + [cnt[k] for k in SUMMARY_COUNTERS] + [dg])) + "\n")
            raw.flush()
        all_d = set().union(*digests.values()) if digests else set()
        meta["workloads"][w.name]["outputs_identical_across_impls_and_reps"] = len(all_d) == 1
        meta["workloads"][w.name]["skipped_impls"] = [i for i in impls if i not in active]
        print(f"{w.name:18s} impls={','.join(active)} identical={len(all_d) == 1}", flush=True)
    raw.close()
    (outdir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()


if __name__ == "__main__":
    main()
