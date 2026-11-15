"""CDS eligibility under ColorFrame's gene model (GROUND_TRUTH_SCHEMA.md section 4).

Checks run in this order; the first failing one is the exclusion reason:
pseudo, partial, strand, alt_start, no_canonical_stop, internal_stop, length.
"""
from collections import OrderedDict

STOPS = {"TAA", "TAG", "TGA"}
COMP = str.maketrans("ACGTacgtNn", "TGCAtgcaNn")
REASONS = ["pseudo", "partial", "strand", "alt_start", "no_canonical_stop", "internal_stop", "length"]


def revcomp(s):
    return s.translate(COMP)[::-1]


def parse_gff3(handle):
    """CDS features grouped by ID (multi-segment CDSs are one record)."""
    recs = OrderedDict()
    for line in handle:
        if line.startswith("##FASTA"):
            break
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) < 9 or f[2] != "CDS":
            continue
        attrs = dict(kv.split("=", 1) for kv in f[8].split(";") if "=" in kv)
        key = (f[0], attrs.get("ID", f"{f[0]}:{f[3]}-{f[4]}:{f[6]}"))
        r = recs.setdefault(key, {"cds_id": key[1], "contig": f[0], "strand": f[6], "segments": [], "attrs": attrs})
        r["segments"].append((int(f[3]), int(f[4])))
    return list(recs.values())


def _sequence(rec, genome):
    contig = genome[rec["contig"]]
    L = len(contig)
    parts = []
    for s, e in sorted(rec["segments"]):
        parts.append(contig[s - 1:e] if e <= L else contig[s - 1:] + contig[:e - L])   # origin-spanning
    seq = "".join(parts).upper()
    return revcomp(seq) if rec["strand"] == "-" else seq


def classify(rec, genome, both_strands=True, max_orf_nt=10**9):
    seq = _sequence(rec, genome)
    a = rec["attrs"]
    start, stop = seq[:3], seq[-3:]
    out = {"cds_id": rec["cds_id"], "contig": rec["contig"], "strand": rec["strand"],
           "start": min(s for s, _ in rec["segments"]), "end": max(e for _, e in rec["segments"]),
           "length_nt": len(seq), "start_codon": start, "stop_codon": stop}
    codons = [seq[i:i + 3] for i in range(0, len(seq) - 3, 3)]
    checks = [
        ("pseudo", a.get("pseudo") == "true"),
        ("partial", a.get("partial") == "true" or "start_range" in a or "end_range" in a),
        ("strand", not both_strands and rec["strand"] != "+"),
        ("alt_start", start != "ATG"),
        ("no_canonical_stop", stop not in STOPS or len(seq) % 3 != 0),
        ("internal_stop", any(c in STOPS for c in codons[1:])),
        ("length", not (6 <= len(seq) <= max_orf_nt)),
    ]
    reason = next((name for name, failed in checks if failed), "")
    out.update(eligible=not reason, exclusion_reason=reason)
    return out


def summarise(rows):
    s = {"total": len(rows), "eligible": sum(r["eligible"] for r in rows)}
    for k in REASONS:
        s[f"excluded_{k}"] = sum(r["exclusion_reason"] == k for r in rows)
    return s
