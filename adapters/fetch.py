"""Download with size and MD5 verification; records SHA-256. Network access only via `opener`."""
import gzip
import hashlib
import os
import urllib.request
from pathlib import Path


class ChecksumError(Exception):
    pass


def _open_url(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "colorframe-bioval/1.0"}), timeout=600)


def fetch(row, root, opener=_open_url):
    """Fetch row['url'] to root/row['dest']; verify bytes and MD5 (when given) before publishing."""
    dest = Path(root) / row["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    md5, sha, n = hashlib.md5(), hashlib.sha256(), 0
    try:
        with opener(row["url"]) as src, open(tmp, "wb") as out:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                out.write(chunk); md5.update(chunk); sha.update(chunk); n += len(chunk)
        if row.get("bytes") not in (None, "", "-") and n != int(row["bytes"]):
            raise ChecksumError(f"{row['dest']}: {n} bytes, expected {row['bytes']}")
        if len(row.get("md5", "")) == 32 and md5.hexdigest() != row["md5"]:
            raise ChecksumError(f"{row['dest']}: md5 {md5.hexdigest()} != {row['md5']}")
        os.replace(tmp, dest)
    finally:
        if tmp.exists():
            tmp.unlink()
    return {"dest": row["dest"], "url": row["url"], "bytes": n, "md5": md5.hexdigest(), "sha256": sha.hexdigest()}


def fastq_stats(path):
    reads = bases = max_len = 0
    with gzip.open(path, "rt") as f:
        for i, line in enumerate(f):
            if i % 4 == 1:
                L = len(line.rstrip("\n"))
                reads += 1; bases += L; max_len = max(max_len, L)
    return {"reads": reads, "bases": bases, "max_len": max_len}
