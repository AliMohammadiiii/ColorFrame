#!/usr/bin/env python3
"""README figures must match what analysis/readme_figures.py produces from the recorded results."""
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as t:
    subprocess.run([sys.executable, str(ROOT / "analysis" / "readme_figures.py"), "--out", t], check=True, capture_output=True)
    fresh = sorted(p.name for p in Path(t).glob("*.svg"))
    stale = [n for n in fresh if not (ROOT / "docs" / "figures" / n).exists()
             or not filecmp.cmp(Path(t) / n, ROOT / "docs" / "figures" / n, shallow=False)]
if stale:
    print("README figures out of date (run: python3 analysis/readme_figures.py):", ", ".join(stale))
    sys.exit(1)
print(f"README figures up to date ({len(fresh)} files)")
