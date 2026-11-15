#!/usr/bin/env python3
"""Each required flag, when omitted, is a usage error (exit 64) naming that flag, in every
implementation. Guards the C++ required-argument check rewritten for GCC 14 (rc2)."""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_cases import CASES, IMPLS  # noqa: E402

REQUIRED = ["--nodes", "--edges", "--policy", "--out", "--summary"]


def main(impls):
    case = CASES / "G01_single_node_orf"
    fails = 0
    with tempfile.TemporaryDirectory() as t:
        full = {"--nodes": str(case / "nodes.tsv"), "--edges": str(case / "edges.tsv"), "--policy": "strict",
                "--out": str(Path(t) / "c.tsv"), "--summary": str(Path(t) / "s.tsv")}
        for impl in impls:
            ok = subprocess.run(IMPLS[impl] + [x for kv in full.items() for x in kv], capture_output=True, text=True)
            if ok.returncode != 0:
                fails += 1
                print(f"FAIL [{impl}] all flags present: exit {ok.returncode}")
            for flag in REQUIRED:
                args = [x for k, v in full.items() if k != flag for x in (k, v)]
                p = subprocess.run(IMPLS[impl] + args, capture_output=True, text=True)
                if p.returncode != 64 or flag not in p.stderr:
                    fails += 1
                    print(f"FAIL [{impl}] missing {flag}: exit {p.returncode}, stderr {p.stderr.strip()[:120]!r}")
            print(f"[{impl}] required-flag checks {'ok' if not fails else 'FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main(sys.argv[1:] or list(IMPLS))
