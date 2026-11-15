"""Machine-readable pilot file list (docs/biological_validation/pilot_files.tsv)."""
import csv
import re
from pathlib import Path

COLUMNS = ["dataset", "sample_id", "kind", "url", "bytes", "md5", "dest"]
KINDS = {"reads", "genome_package", "reference_fasta", "reference_gff"}
MD5 = re.compile(r"^[0-9a-f]{32}$")


def load(path):
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    if not rows or list(rows[0].keys()) != COLUMNS:
        raise ValueError(f"{path}: expected columns {COLUMNS}")
    seen = set()
    for r in rows:
        if r["kind"] not in KINDS:
            raise ValueError(f"unknown kind {r['kind']!r}")
        if r["kind"] == "reads" and not MD5.match(r["md5"]):
            raise ValueError(f"reads row needs an MD5: {r['dest']}")
        if r["kind"] == "genome_package" and r["md5"] != "package":
            raise ValueError(f"genome packages are verified by their md5sum.txt: {r['dest']}")
        if not r["url"].startswith("https://"):
            raise ValueError(f"https only: {r['url']}")
        if r["dest"] in seen or Path(r["dest"]).is_absolute() or ".." in Path(r["dest"]).parts:
            raise ValueError(f"bad or duplicate dest {r['dest']!r}")
        seen.add(r["dest"])
    return rows
