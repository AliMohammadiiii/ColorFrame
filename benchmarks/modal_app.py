"""ColorFrame on Modal: the authoritative environment for correctness checks and benchmarks.

    modal run benchmarks/modal_app.py                       # full pipeline
    modal run benchmarks/modal_app.py --reps 7 --warmup 2 --skip "python:stress_s800000"
    modal run benchmarks/modal_app.py --stage analysis --run-id <existing results/modal/ID>

Credentials come from the active Modal profile (`modal token set` / `modal profile activate`);
nothing secret is read or written by this file. See MODAL_EXECUTION.md.

Pipeline inside one pinned container (cpu=1, 4 GiB):
  1. fixture consistency + conformance of all three implementations (39 cases each)
  2. generate workloads (seed 42) and require byte-identical outputs across languages
  3. RQ1 recovery evaluation
  4. benchmarks: warm-up + measured runs, randomised order, wall time / phase times / peak RSS
Then, in a separate R container, analysis/analysis.R turns the results into tables/figures.
"""
import io
import os
import subprocess
import tarfile
import time
from pathlib import Path

import modal

REPO = Path(__file__).resolve().parent.parent
RUST_TOOLCHAIN = "1.99.1"      # must match rust/rust-toolchain.toml
PYTHON_VERSION = "3.12"


def _git(*args):
    try:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        return ""


# Evaluated at import on the client; inside the container the env vars below carry the values.
COMMIT = os.environ.get("COLORFRAME_COMMIT") or _git("rev-parse", "HEAD") or "unknown"
DIRTY = os.environ.get("COLORFRAME_DIRTY") or ("1" if _git("status", "--porcelain") else "0")

IGNORE = [".git", ".git/**", ".worktrees", ".worktrees/**", "private", "private/**", "generated/**",
          "results/**", "reports/**", "cpp/build", "cpp/build/**", "rust/target", "rust/target/**",
          "**/__pycache__", "**/.DS_Store", "out/**"]

bench_image = (
    modal.Image.debian_slim(python_version=PYTHON_VERSION)
    .apt_install("build-essential", "curl", "ca-certificates", "git")
    .run_commands(
        "curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal "
        f"--default-toolchain {RUST_TOOLCHAIN} -c rustfmt -c clippy"
    )
    .env({"PATH": "/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
          "COLORFRAME_ENV": "modal", "COLORFRAME_COMMIT": COMMIT, "COLORFRAME_DIRTY": DIRTY,
          "CXX": "g++"})
    .add_local_dir(REPO, "/repo", copy=True, ignore=IGNORE)
    .run_commands("make -C /repo/cpp CXX=g++", "cd /repo/rust && cargo build --release --locked")
)

r_image = (
    modal.Image.debian_slim(python_version=PYTHON_VERSION)
    .apt_install("r-base-core")
    .add_local_dir(REPO / "analysis", "/analysis", copy=True)
)

app = modal.App("colorframe-bench")


def _sh(cmd, log, required=True):
    log.write(f"$ {cmd}\n")
    p = subprocess.run(cmd, shell=True, cwd="/repo", capture_output=True, text=True)
    log.write(p.stdout + p.stderr + f"[exit {p.returncode}]\n")
    log.flush()
    if p.returncode != 0 and required:
        raise RuntimeError(f"command failed: {cmd}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p.stdout


def _tar(path: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.add(path, arcname=".")
    return buf.getvalue()


@app.function(image=bench_image, cpu=1.0, memory=4096, timeout=4 * 3600)
def pipeline(reps: int = 7, warmup: int = 2, skip: str = "") -> bytes:
    out = Path("/repo/results/run")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(out / "pipeline.log", "w") as log:
        log.write(f"commit={COMMIT} dirty={os.environ.get('COLORFRAME_DIRTY')}\n")
        # Environment capture is informational and must never discard results.
        _sh("python3 --version; g++ --version | head -1; rustc --version; nproc; "
            "grep -m1 'model name' /proc/cpuinfo; grep -E 'MemTotal|MemAvailable' /proc/meminfo", log,
            required=False)
        _sh("python3 tests/check_fixtures.py", log)
        _sh("python3 tests/run_cases.py --impl all", log)
        _sh("python3 benchmarks/generate_workloads.py", log)
        _sh(f"python3 tests/cross_language.py --out {out}/cross_language.tsv", log)
        _sh(f"python3 benchmarks/evaluate_rq1.py --impl rust --out {out}/rq1_recovery.tsv", log)
        skip_arg = f"--skip {skip}" if skip.strip() else ""
        _sh(f"python3 benchmarks/run_benchmarks.py --out {out} --reps {reps} --warmup {warmup} {skip_arg}", log)
        _sh(f"cat /proc/cpuinfo > {out}/cpuinfo.txt; cat /proc/meminfo > {out}/meminfo.txt", log,
            required=False)
        log.write(f"container_wall_seconds={time.time() - t0:.1f}\n")
    return _tar(out)


@app.function(image=r_image, cpu=1.0, memory=2048, timeout=900)
def analysis(results_tar: bytes, usage_csv: bytes) -> bytes:
    work = Path("/work")
    res, fig = work / "results", work / "figures"
    res.mkdir(parents=True)
    fig.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(results_tar), mode="r:gz") as tf:
        tf.extractall(res, filter="data")
    (res / "agent_usage.csv").write_bytes(usage_csv)
    p = subprocess.run(["Rscript", "/analysis/analysis.R", str(res), str(fig)], capture_output=True, text=True)
    (fig / "analysis.log").write_text(p.stdout + p.stderr + f"\n[exit {p.returncode}]\n")
    v = subprocess.run(["R", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    (fig / "r_version.txt").write_text(v + "\n")
    return _tar(fig)


def _untar(data: bytes, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        tf.extractall(dest, filter="data")


@app.local_entrypoint()
def main(stage: str = "all", reps: int = 7, warmup: int = 2, skip: str = "", run_id: str = "",
         results_dir: str = ""):
    """results_dir (analysis stage only): analyse e.g. results/local/<id> instead of a Modal run."""
    run_id = run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rdir = (REPO / results_dir) if results_dir else REPO / "results" / "modal" / run_id
    if stage in ("all", "bench"):
        if DIRTY == "1":
            print("WARNING: working tree has uncommitted changes; results will be marked dirty")
        _untar(pipeline.remote(reps=reps, warmup=warmup, skip=skip), rdir)
        print(f"benchmark results -> {rdir}")
    if stage in ("all", "analysis"):
        usage = (REPO / "results" / "agent_usage.csv").read_bytes()
        fdir = REPO / "reports" / "figures" / f"{rdir.parent.name}_{rdir.name}"
        _untar(analysis.remote(_tar(rdir), usage), fdir)
        print(f"analysis outputs -> {fdir}")
