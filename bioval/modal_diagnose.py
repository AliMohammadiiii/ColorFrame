"""Pilot diagnostic: are draft-vs-complete differences nanopore assembly errors or real
(stock) differences? Per ECOR isolate, on Modal:
  1. draft vs complete (minimap2 asm5 --cs): mismatches vs indels, homopolymer indels;
  2. the isolate's own Illumina reads mapped to its complete genome (minimap2 sr, bcftools,
     haploid): confident disagreements = places where the complete genome is not supported.
    modal run bioval/modal_diagnose.py
"""
import csv
import time
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent.parent
image = (modal.Image.debian_slim(python_version="3.12").apt_install("minimap2", "samtools", "bcftools")
         .add_local_dir(ROOT / "adapters", "/app/adapters", ignore=["__pycache__"]))
volume = modal.Volume.from_name("colorframe-bioval")
app = modal.App("colorframe-bioval-diagnose", image=image)


@app.function(volumes={"/vol": volume}, cpu=8.0, memory=16384, timeout=3600)
def diagnose(sample: str) -> dict:
    import subprocess
    import sys
    sys.path.insert(0, "/app")
    from adapters import diff
    w = Path("/vol/work/ecor") / sample
    cfa = next((w / "complete").rglob("*_genomic.fna")); dfa = next((w / "draft").rglob("*_genomic.fna"))
    r1, r2 = sorted(Path(f"/vol/raw/ecor/{sample}").glob("*_[12].fastq.gz"))
    genome, name = {}, None
    for line in open(cfa):
        if line.startswith(">"):
            name = line[1:].split()[0]; genome[name] = []
        else:
            genome[name].append(line.strip())
    genome = {k: "".join(v) for k, v in genome.items()}
    sh = lambda c: subprocess.run(c, shell=True, check=True, capture_output=True, text=True).stdout
    events = []
    for line in sh(f"minimap2 -cx asm5 --cs -t 8 {cfa} {dfa}").splitlines():
        f = line.split("\t")
        if "tp:A:P" not in f[12:]:
            continue
        cs = next(x[5:] for x in f[12:] if x.startswith("cs:Z:"))
        if f[4] == "-":   # cs is relative to the target forward strand either way
            pass
        events += diff.parse_cs(cs, genome[f[5]], int(f[7]))
    a = diff.summarise(events)
    tmp = Path("/tmp") / sample; tmp.mkdir(exist_ok=True)
    sh(f"minimap2 -ax sr -t 8 {cfa} {r1} {r2} | samtools sort -@4 -o {tmp}/r.bam - && samtools index {tmp}/r.bam")
    flag = sh(f"samtools flagstat {tmp}/r.bam")
    mapped = next(l for l in flag.splitlines() if " mapped (" in l and "primary" not in l)
    sh(f"samtools faidx {cfa}")
    sh(f"bcftools mpileup -Ou -f {cfa} -d 1000 {tmp}/r.bam | bcftools call --ploidy 1 -mv -Ov -o {tmp}/v.vcf")
    v = diff.vcf_summary(open(f"{tmp}/v.vcf"), genome, min_qual=30)
    size = sum(len(s) for s in genome.values())
    return {"sample_id": sample, "genome_bp": size,
            "draft_mismatches": a["mismatches"], "draft_insertions": a["insertions"], "draft_deletions": a["deletions"],
            "draft_indels_homopolymer": a["indels_homopolymer"],
            "reads_mapped": mapped.split("(")[1].split(":")[0].strip(),
            "illumina_snps": v["snps"], "illumina_indels": v["indels"], "illumina_indels_homopolymer": v["indels_homopolymer"],
            "illumina_disagreements_per_100kb": round((v["snps"] + v["indels"]) / size * 1e5, 2),
            "versions": sh("minimap2 --version").strip() + "; " + sh("bcftools --version").splitlines()[0]}


@app.local_entrypoint()
def main():
    rows = list(diagnose.map(["ECOR01", "ECOR56", "ECOR69", "ECOR72"]))
    d = ROOT / "results" / "bioval" / ("diagnostic_" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "identity_diagnostic.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"results -> {d}")
    for r in rows:
        print(r)
