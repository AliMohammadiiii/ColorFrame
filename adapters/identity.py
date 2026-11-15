"""Stock-identity gate from minimap2 PAF (draft assembly vs complete genome)."""
from collections import defaultdict

MIN_IDENTITY, MIN_ALIGNED_FRACTION = 0.999, 0.98


def from_paf(handle):
    """Primary alignments only: identity = matches / block length; aligned fraction = union of
    query intervals / total query length."""
    qlen, ivals, match, block = {}, defaultdict(list), 0, 0
    for line in handle:
        f = line.rstrip("\n").split("\t")
        if len(f) < 12 or "tp:A:P" not in f[12:]:
            continue
        qlen[f[0]] = int(f[1])
        ivals[f[0]].append((int(f[2]), int(f[3])))
        match += int(f[9]); block += int(f[10])
    covered = 0
    for q, iv in ivals.items():
        end = -1
        for s, e in sorted(iv):
            if e > end:
                covered += e - max(s, end); end = e
    total = sum(qlen.values())
    return {"identity": match / block if block else 0.0, "aligned_fraction": covered / total if total else 0.0,
            "aligned_bases": covered, "query_bases": total}


def passes(r):
    return r["identity"] >= MIN_IDENTITY and r["aligned_fraction"] >= MIN_ALIGNED_FRACTION
