#!/usr/bin/env python3
"""Release-archive privacy and completeness check (v1.0.1, mission section 12).

    python3 tests/check_release_archive.py ARCHIVE.zip|.tar.gz

Fails if the archive contains private material, VCS internals, build artefacts, OS metadata,
caches or credential-like strings, or lacks the files needed to reproduce the project.
"""
import re
import sys
import tarfile
import zipfile

FORBIDDEN = [r"(^|/)private/", r"(^|/)\.git/", r"(^|/)\.worktrees/", r"(^|/)cpp/build/", r"(^|/)rust/target/",
             r"(^|/)__MACOSX/", r"\.DS_Store$", r"(^|/)__pycache__/", r"\.pyc$", r"(^|/)generated/(?!README\.md$)",
             r"(^|/)\.env", r"\.modal\.toml$", r"\.pem$", r"(?i)johan", r"(?i)transcript", r"(?i)defen[cs]e_notes"]
SECRET = re.compile(rb"(ak-[A-Za-z0-9]{12,}|as-[A-Za-z0-9]{12,}|MODAL_TOKEN_SECRET\s*=\s*\S+|-----BEGIN [A-Z ]*PRIVATE KEY)")
REQUIRED = ["README.md", "ALGORITHM_SPEC.md", "INPUT_OUTPUT_SCHEMA.md", "Makefile", "python/colorframe.py",
            "cpp/Makefile", "rust/Cargo.toml", "rust/Cargo.lock", "tests/run_cases.py",
            "benchmarks/generate_workloads.py", "benchmarks/modal_app.py", "analysis/analysis.R",
            "fixtures/cases/G01_single_node_orf/nodes.tsv", "reports/TECHNICAL_REPORT.md",
            "REMEDIATION_REPORT.md", "SECURITY.md"]


def entries(path):
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        return [(n, (lambda n=n: z.read(n))) for n in z.namelist() if not n.endswith("/")]
    t = tarfile.open(path)
    return [(m.name, (lambda m=m: t.extractfile(m).read())) for m in t.getmembers() if m.isfile()]


def main(path):
    items = entries(path)
    prefix = items[0][0].split("/")[0] + "/" if items and all(n.startswith(items[0][0].split("/")[0] + "/") for n, _ in items) else ""
    names = [n[len(prefix):] for n, _ in items]
    problems = [f"forbidden path: {n}" for n in names for pat in FORBIDDEN if re.search(pat, n)]
    for (n, read), rel in zip(items, names):
        if SECRET.search(read()) and rel != "SECURITY.md" and not rel.startswith("tests/check_release_archive.py"):
            problems.append(f"credential-like string in {rel}")
    problems += [f"missing required file: {r}" for r in REQUIRED if r not in names]
    for p in problems[:40]:
        print("FAIL", p)
    print(f"{len(names)} files checked; {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(sys.argv[1])
