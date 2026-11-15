"""Biological-validation pilot, stage 1 (data): verified download, read sanity, identity gate,
CDS eligibility. Runs entirely on Modal; data stay on the Modal Volume `colorframe-bioval`.

    modal run bioval/modal_pilot.py

Writes small result tables to results/bioval/pilot_<UTC>/ locally. No credentials are read or
written by this file.
"""
import csv
import json
import time
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent.parent
BV = ROOT / "docs" / "biological_validation"
VOL = "/vol"

image = (modal.Image.debian_slim(python_version="3.12")
         .apt_install("minimap2", "unzip")
         .add_local_dir(ROOT / "adapters", "/app/adapters", ignore=["__pycache__"])
         .add_local_file(BV / "pilot_files.tsv", "/app/pilot_files.tsv")
         .add_local_file(BV / "evidence" / "ecor_pilot_runs.tsv", "/app/ecor_pilot_runs.tsv")
         .add_local_file(BV / "evidence" / "debourcy_runs.tsv", "/app/debourcy_runs.tsv"))
volume = modal.Volume.from_name("colorframe-bioval", create_if_missing=True)
app = modal.App("colorframe-bioval-pilot", image=image)


@app.function(volumes={VOL: volume}, cpu=1.0, memory=1024, timeout=3600, retries=2)
def fetch_one(row: dict) -> dict:
    import sys
    sys.path.insert(0, "/app")
    from adapters import fetch
    raw = Path(VOL) / "raw"
    done = raw / (row["dest"] + ".fetch.json")
    if done.exists() and (raw / row["dest"]).exists():
        return json.loads(done.read_text()) | {"skipped": True}
    t0 = time.time()
    try:
        rec = fetch.fetch(row, raw)
    except Exception as e:  # re-raise as a plain, picklable error naming the file
        raise RuntimeError(f"{row['dest']}: {type(e).__name__}: {e}") from None
    rec["seconds"] = round(time.time() - t0, 1)
    rec["retrieved_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    done.write_text(json.dumps(rec))
    volume.commit()
    return rec


@app.function(volumes={VOL: volume}, cpu=4.0, memory=8192, timeout=3600)
def analyse() -> dict:
    import subprocess
    import sys
    import zipfile
    sys.path.insert(0, "/app")
    from adapters import cds, fetch, identity
    volume.reload()
    raw, work = Path(VOL) / "raw", Path(VOL) / "work"
    out = {"tool_versions": {"minimap2": subprocess.run(["minimap2", "--version"], capture_output=True, text=True).stdout.strip()}}

    # 1. read sanity: bases per run vs ENA base_count
    expected = {}
    for f in ("/app/ecor_pilot_runs.tsv", "/app/debourcy_runs.tsv"):
        for r in csv.reader(open(f), delimiter="\t"):
            if r[0].startswith("SRR"):
                expected[r[0]] = int(r[4])
    reads = []
    for p in sorted(raw.rglob("*.fastq.gz")):
        run = p.name.split("_")[0]
        st = fetch.fastq_stats(p)
        reads.append({"file": str(p.relative_to(raw)), "run": run, **st})
    by_run = {}
    for r in reads:
        by_run.setdefault(r["run"], 0)
        by_run[r["run"]] += r["bases"]
    out["read_sanity"] = [{"run": k, "bases_observed": v, "bases_ena": expected.get(k), "match": v == expected.get(k)}
                          for k, v in sorted(by_run.items())]
    out["read_files"] = reads

    # 2. unpack NCBI packages (verify bundled md5sum.txt)
    def unpack(z, dest):
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(dest)
        bad = subprocess.run("cd {} && md5sum -c --quiet md5sum.txt".format(dest), shell=True, capture_output=True, text=True)
        if bad.returncode != 0:
            raise RuntimeError(f"md5sum.txt check failed for {z}: {bad.stdout[-500:]}")
        return dest
    gate, elig, summaries = [], [], []
    for sdir in sorted((raw / "ecor").iterdir()):
        sample = sdir.name
        comp = next(sdir.glob("GCF_*.zip")); draft = next(sdir.glob("GCA_*_draft.zip"))
        cdir = unpack(comp, work / "ecor" / sample / "complete")
        ddir = unpack(draft, work / "ecor" / sample / "draft")
        cfa = next(cdir.rglob("*_genomic.fna")); dfa = next(ddir.rglob("*_genomic.fna"))
        gff = next(cdir.rglob("genomic.gff"))
        # 3. identity gate: draft contigs (query) against the complete genome (target)
        paf = work / "ecor" / sample / "draft_vs_complete.paf"
        subprocess.run(f"minimap2 -cx asm5 -t 4 {cfa} {dfa} > {paf}", shell=True, check=True, capture_output=True)
        g = identity.from_paf(open(paf))
        gate.append({"sample_id": sample, "complete": comp.stem, "draft": draft.stem.replace("_draft", ""), **g,
                     "passes": identity.passes(g)})
        # 4. CDS eligibility from the complete genome + PGAP GFF
        genome, name = {}, None
        for line in open(cfa):
            if line.startswith(">"):
                name = line[1:].split()[0]; genome[name] = []
            else:
                genome[name].append(line.strip())
        genome = {k: "".join(v) for k, v in genome.items()}
        recs = cds.parse_gff3(open(gff))
        for both in (False, True):
            for mx in (1200, 3000, 6000):
                rows = [cds.classify(r, genome, both_strands=both, max_orf_nt=mx) for r in recs]
                summaries.append({"sample_id": sample, "both_strands": both, "max_orf_nt": mx, **cds.summarise(rows)})
        for r in (cds.classify(x, genome, both_strands=True, max_orf_nt=6000) for x in recs):
            elig.append({"sample_id": sample, **r})
    out["identity_gate"], out["eligibility_summary"], out["cds_table"] = gate, summaries, elig
    volume.commit()
    return out


@app.local_entrypoint()
def main():
    import sys
    sys.path.insert(0, str(ROOT))
    from adapters import pilot_files
    rows = pilot_files.load(BV / "pilot_files.tsv")
    t0 = time.time()
    results = list(fetch_one.map(rows, order_outputs=False, return_exceptions=True))
    failed = [str(r) for r in results if isinstance(r, BaseException)]
    fetched = [r for r in results if not isinstance(r, BaseException)]
    print(f"fetched {len(fetched)}/{len(rows)}")
    if failed:
        for f in failed:
            print("FAILED", f)
        raise SystemExit(1)
    res = analyse.remote()
    res["fetch_wall_s"] = round(time.time() - t0, 1)
    d = ROOT / "results" / "bioval" / ("pilot_" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    d.mkdir(parents=True, exist_ok=True)

    def tsv(name, recs):
        if recs:
            with open(d / name, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(recs[0].keys()), delimiter="\t", lineterminator="\n", extrasaction="ignore")
                w.writeheader(); w.writerows(recs)
    tsv("fetch_log.tsv", sorted(fetched, key=lambda r: r["dest"]))
    tsv("read_sanity.tsv", res["read_sanity"])
    tsv("identity_gate.tsv", res["identity_gate"])
    tsv("cds_eligibility_summary.tsv", res["eligibility_summary"])
    tsv("cds_eligibility.tsv", res["cds_table"])
    (d / "run.json").write_text(json.dumps({"tool_versions": res["tool_versions"], "volume": "colorframe-bioval",
                                            "fetch_wall_s": res["fetch_wall_s"]}, indent=2))
    print(f"results -> {d}")
