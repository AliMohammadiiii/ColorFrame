# Download Plan (pilot only; NOTHING downloaded yet)

**Status:** Proposal, 2026-11-15. No read or genome data has been downloaded. Every number
below comes from ENA/NCBI metadata retrieved on 2026-11-15. Downloads start only after Ali
approves `BIOLOGICAL_VALIDATION_DECISION.md`.

## 1. Scope and size

| Item | Files | Bytes |
|---|---|---|
| ECOR Illumina reads, 4 isolates | 8 fastq.gz | 905,242,623 |
| de Bourcy reads: unamplified bulk + 3 MDA single cells | 8 fastq.gz | 928,043,766 |
| ECOR complete genomes + PGAP annotation, 4 isolates | 4 NCBI Datasets packages (genome FASTA, GFF3, CDS FASTA) | ~12 MB (NCBI estimate: 3 MB each) |
| DH10B proxy reference CP000948.1 (FASTA + GFF3) | 2 files | ~10 MB (estimate) |
| **Total** | | **≈ 1.86 GB** |

Not downloaded: ONT raw signal (any dataset), full projects, GORG-Dark, CAMI reads, MBARC-26,
BMock12, HiFi mock. The CAMISIM data are generated from the 4 ECOR genomes, not downloaded.

## 2. Exact read files (ENA, HTTPS)

| Dataset | Run | URL | Bytes | MD5 (ENA) |
|---|---|---|---|---|
| ECOR | SRR3989531 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR398/001/SRR3989531/SRR3989531_1.fastq.gz` | 114682647 | `7396d5ef62e826675a374e876124e810` |
| ECOR | SRR3989531 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR398/001/SRR3989531/SRR3989531_2.fastq.gz` | 116629770 | `03d504e86cfcf689a28a525b0e372ba4` |
| ECOR | SRR7819142 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR781/002/SRR7819142/SRR7819142_1.fastq.gz` | 95125255 | `3cb5bc0bdbe92e97cc2e07260c89b427` |
| ECOR | SRR7819142 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR781/002/SRR7819142/SRR7819142_2.fastq.gz` | 98085024 | `360ce561dc935614d4f81ccc5897ba3d` |
| ECOR | SRR3989539 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR398/009/SRR3989539/SRR3989539_1.fastq.gz` | 115499358 | `1f570243748ebd9c81c9ecf1555e2b96` |
| ECOR | SRR3989539 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR398/009/SRR3989539/SRR3989539_2.fastq.gz` | 118851812 | `f9070b018606f0a380deef8acc083d6c` |
| ECOR | SRR7819146 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR781/006/SRR7819146/SRR7819146_1.fastq.gz` | 121381227 | `7ec9253907a1e45ed7e2fcbed05a8870` |
| ECOR | SRR7819146 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR781/006/SRR7819146/SRR7819146_2.fastq.gz` | 124987530 | `f46bef76659e8a9b952c3d20a37061e1` |
| de Bourcy MDA_Cell_3 | SRR1614006 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/006/SRR1614006/SRR1614006_1.fastq.gz` | 130540151 | `b31ab92675dfdbb3c45895b203eb4ad6` |
| de Bourcy MDA_Cell_3 | SRR1614006 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/006/SRR1614006/SRR1614006_2.fastq.gz` | 150563361 | `0b4d1f8e22f933de455107c535227c99` |
| de Bourcy MDA_Cell_2 | SRR1614005 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/005/SRR1614005/SRR1614005_1.fastq.gz` | 87053807 | `08c4441af0093997c9723c2f91bc0e4a` |
| de Bourcy MDA_Cell_2 | SRR1614005 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/005/SRR1614005/SRR1614005_2.fastq.gz` | 109173835 | `d36c2f11d609428241ee783e207b2ef8` |
| de Bourcy Bulk_DNA_Reference | SRR1613979 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/009/SRR1613979/SRR1613979_1.fastq.gz` | 78705223 | `91397fa211a771227b2e6810af87ee98` |
| de Bourcy Bulk_DNA_Reference | SRR1613979 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/009/SRR1613979/SRR1613979_2.fastq.gz` | 89767125 | `76fe7a9134c6819f7955ac92b4fed104` |
| de Bourcy MDA_Cell_1 | SRR1614004 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/004/SRR1614004/SRR1614004_1.fastq.gz` | 140137196 | `def4de3f848d1bba9ae76d198825a36a` |
| de Bourcy MDA_Cell_1 | SRR1614004 | `https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR161/004/SRR1614004/SRR1614004_2.fastq.gz` | 142103068 | `c080747a6feb96db9073dbb56effd6fb` |

## 3. Genomes and annotation (NCBI Datasets v2)

```
https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{ACC}/download?include_annotation_type=GENOME_FASTA&include_annotation_type=GENOME_GFF&include_annotation_type=CDS_FASTA
ACC ∈ GCF_062083226.1 (ECOR01), GCF_062082974.1 (ECOR56), GCF_062082961.1 (ECOR69), GCF_062082958.1 (ECOR72)
```

Plus the matching FDA draft assemblies GCA_003334405.1, GCA_003334485.1, GCA_003334435.1 and
GCA_003334425.1 (genome FASTA only; for the stock-identity gate in §5).

DH10B proxy: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=CP000948.1&rettype=fasta`
and `rettype=gff3`.

## 4. Tools, storage and checksums

- **Where:** a Modal Volume `colorframe-bioval`, path `/raw/<dataset>/<accession>/`, created on
  approval. Nothing goes into Git: `generated/` and `data/` stay ignored, and the archive checker
  rejects them.
- **How:** `curl --fail --retry 3` over HTTPS inside a Modal function (no local copy needed),
  followed by `md5sum -c` against the ENA MD5s above. A mismatch aborts the run and is logged.
  The NCBI packages are verified with their bundled `md5sum.txt`.
- **Recorded:** SHA-256 of every file, the retrieval UTC time and the exact URL, in
  `provenance.json` (`GROUND_TRUTH_SCHEMA.md` §3).
- **Credentials:** the Modal token is read from Modal's own local configuration or environment.
  It is never printed or written to the repository. The token exposed earlier in chat must be
  revoked (an owner action) before this run.

## 5. Gates before any analysis

1. **Stock identity (ECOR):** each FDA draft assembly must agree with its complete genome
   (≥ 99.9% ANI and ≥ 98% of draft k-mers present). Otherwise the isolate is excluded and
   replaced by the next candidate in `evidence/ecor_samples.tsv`. Reason: the reads and the
   complete genomes come from different labs and possibly different stocks.
2. **Read sanity:** read counts and lengths match the ENA metadata.
3. **de Bourcy:** the bulk-library assembly is compared with DH10B and the differences are
   recorded. Only the bulk assembly serves as the same-stock reference.

## 6. Reproduction

`adapters/fetch.py --manifest docs/biological_validation/DATASET_MANIFEST.csv --dataset ecor
--pilot` (to be written after approval, test-first) re-creates exactly the files above and
fails on any checksum difference.
