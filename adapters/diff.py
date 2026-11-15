"""Classify assembly differences (minimap2 cs tags) and read-based variant calls (VCF),
separating mismatches from indels and flagging homopolymer indels (run of >= 3 identical
target bases at the site), the typical nanopore consensus error."""
import re

CS = re.compile(r"(:\d+|\*[a-z][a-z]|[+\-][A-Za-z]+)")


def _run_length(t, pos, base):
    """Length of the run of `base` in t touching position pos (or pos-1)."""
    base = base.upper()
    i = pos
    while i > 0 and t[i - 1].upper() == base:
        i -= 1
    j = pos
    while j < len(t) and t[j].upper() == base:
        j += 1
    return j - i


def _homopolymer(t, pos, seq):
    return len(set(seq.upper())) == 1 and _run_length(t, pos, seq[0]) >= 3


def parse_cs(cs, target, tstart):
    ev, p = [], tstart
    for op in CS.findall(cs):
        if op[0] == ":":
            p += int(op[1:])
        elif op[0] == "*":
            ev.append({"type": "mismatch", "pos": p, "homopolymer": False}); p += 1
        elif op[0] == "-":
            ev.append({"type": "deletion", "pos": p, "len": len(op) - 1, "homopolymer": _homopolymer(target, p, op[1:])})
            p += len(op) - 1
        else:
            ev.append({"type": "insertion", "pos": p, "len": len(op) - 1, "homopolymer": _homopolymer(target, p, op[1:])})
    return ev


def summarise(ev):
    return {"mismatches": sum(e["type"] == "mismatch" for e in ev),
            "insertions": sum(e["type"] == "insertion" for e in ev),
            "deletions": sum(e["type"] == "deletion" for e in ev),
            "indels_homopolymer": sum(e["homopolymer"] for e in ev if e["type"] != "mismatch")}


def vcf_summary(handle, genome, min_qual=30):
    s = {"snps": 0, "indels": 0, "indels_homopolymer": 0}
    for line in handle:
        if line.startswith("#"):
            continue
        f = line.rstrip("\n").split("\t")
        qual = float(f[5]) if f[5] != "." else 0.0
        gt = f[9].split(":")[0] if len(f) > 9 else "1"
        if qual < min_qual or gt in ("0", "0/0", "."):
            continue
        ref, alt = f[3], f[4].split(",")[0]
        if len(ref) == len(alt) == 1:
            s["snps"] += 1
        else:
            s["indels"] += 1
            changed = ref[1:] if len(ref) > len(alt) else alt[1:]
            if _homopolymer(genome[f[0]], int(f[1]), changed):   # 1-based POS -> 0-based next base
                s["indels_homopolymer"] += 1
    return s
