"""C++ portability check on GCC 14 (rc2, audit finding F5). Runs on Modal.

    modal run tests/modal_gcc14_build.py

Uses the official `gcc:14` image and the UNCHANGED cpp/Makefile (which keeps
-Wall -Wextra -Wpedantic -Werror), then runs the C++ unit tests, all fixture cases and the
required-flag CLI checks. Exits non-zero on any failure.
"""
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent.parent
image = (modal.Image.from_registry("gcc:14", add_python="3.12")
         .add_local_dir(ROOT / "cpp", "/w/cpp", ignore=["build"])
         .add_local_dir(ROOT / "fixtures", "/w/fixtures")
         .add_local_dir(ROOT / "tests", "/w/tests", ignore=["__pycache__"]))
app = modal.App("colorframe-gcc14-check", image=image)


@app.function(cpu=2.0, memory=2048, timeout=900)
def check() -> tuple[int, str]:
    import subprocess
    out, rc = [], 0
    for cmd in ["g++ --version | head -1", "grep '^CXXFLAGS' cpp/Makefile",
                "make -C cpp CXX=g++ all", "make -C cpp CXX=g++ test",
                "python3 tests/run_cases.py --impl cpp", "python3 tests/test_cli_required_flags.py cpp"]:
        p = subprocess.run(cmd, shell=True, cwd="/w", capture_output=True, text=True)
        out.append(f"$ {cmd}\n{p.stdout[-1500:]}{p.stderr[-3000:]}[exit {p.returncode}]")
        if p.returncode != 0:
            rc = p.returncode
            break
    return rc, "\n".join(out)


@app.local_entrypoint()
def main():
    rc, log = check.remote()
    print(log)
    if rc:
        raise SystemExit(rc)
