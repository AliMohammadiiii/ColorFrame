# B findings: public bacterial datasets, checked at primary sources (2026-11-15)

Status labels: **V** = Verified (source given), **PV** = Partially verified, **NV** = Not verified, **NA** = Not available, **U** = Unclear.
Evidence files are in this directory (`bioval/B/`). Metadata only; no read files were downloaded.

---

## 1. ECOR (E. coli Reference collection)

### Corrections to the exploratory notes
- **PRJNA230969 is not an ECOR project.** It is the FDA/CFSAN *GenomeTrakr* E. coli surveillance BioProject, titled "GenomeTrakr Project: US Food and Drug Administration" (organism *Escherichia*; parent PRJNA230919, which sits under PRJNA593772). It holds many thousands of surveillance isolates. The 72 FDA ECOR genomes were deposited **inside** it. **V**: `bp_esummary.json`, `ecor_ncbi_datasets_report.json` (bioproject_lineage). To select ECOR from it you need the accession list below, not the BioProject alone.
- "Approximately 72" is in fact **exactly 72** isolates (Ochman & Selander 1984; Patel et al. 2018 sequenced "all 72"). **V**: `ecor_patel2018_MRA_fulltext.xml`.
- **A newer and better ECOR resource exists:** BioProject **PRJNA1543032**, "Complete genome sequencing of the Escherichia coli Reference (ECOR) collection using Oxford Nanopore sequencing", submitted by Mississippi State University (registered 2026-10-12; assemblies released 2026-11-10). It has 72 complete genomes. **V**: `ecor_PRJNA1543032_esummary.json`, `ecor_PRJNA1543032_datasets_report_genbank.json`.

### 1a. FDA Illumina drafts (Patel et al. 2018)
- Publication: Patel IR, Gangiredla J, Mammel MK, Lampel KA, Elkins CA, Lacher DW (2018), "Draft Genome Sequences of the Escherichia coli Reference (ECOR) Collection", *Microbiol Resour Announc* 7:e01133-18, doi:10.1128/MRA.01133-18, PMC6256646. **V**: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6256646/fullTextXML
- Accessions: WGS QOWM00000000–QOZF00000000 (ECOR59 = QOZF, out of order). GCA_0033xxxxx.1, each paired with a current GCF_. **V**: 72/72 GenBank assemblies, all with a GCF (`ecor_ncbi_datasets_report.json`, `ecor_ena_assemblies.tsv`).
- BioSamples: 72 distinct SAMN (SAMN04158xxx, SAMN049138xx, SAMN05439xxx, SAMN09633xxx). Strain field "MOD1-ECOR<n>", alias "ECOR<n>; CFSAN0xxxxx". Note that the BioSample metadata is generic GenomeTrakr content (host "Homo sapiens", geo "USA") and does not record the original ECOR provenance. **V** (datasets report).
- Runs: one run per isolate is cited in the paper (Table 1). ECOR46 (SAMN04913893) has a second, larger run: SRR3951511 (NextSeq, 2.40 Gbp) alongside the cited SRR3987677 (MiSeq). Every other isolate has exactly one run. **V**: `ecor_ena_runs.tsv`, `ecor_ena_runs_by_sample.tsv`.
- Platform: Illumina NextSeq 500 (62 runs, 2×150) and MiSeq (10 runs, 2×250). Libraries were Nextera XT from DNA of pure cultures. **V**.
- Assembly level: **Contig** for all 72; 47–354 contigs; N50 58–467 kb; length 4.51–5.59 Mb; SPAdes 3.8.2 or CLC. **V**.
- Annotation: GenBank PGAP 4.6 (2018), plus current RefSeq GCF annotation (e.g. GCF_003333785.1-RS_2025_06_24). **V**.
- Quality flags: NCBI `atypical` = none on all 72. ANI taxonomy check OK on 72/72. CheckM completeness 96.81–99.56%, contamination 0.15–1.08%. **V**.
- Volume: 72 cited runs = 77.44 Gbp, about 50.3 GB FASTQ (gz) on ENA. **V**: `ecor_ena_runs.tsv`.

### 1b. ONT complete genomes (PRJNA1543032)
- 72 BioSamples (SAMN64169118–SAMN64169189, strain "ECOR01"…"ECOR72", provider STEC Center, Michigan State University). There is 1 ONT PromethION run per sample (SRR4115xxxx), 57.94 Gbp in total and about 43.0 GB FASTQ. **V**: `ecor_PRJNA1543032_ena_runs.tsv`, `ecor_PRJNA1543032_sra_runinfo.csv`.
- 72 GCA assemblies (GCA_06208xxxx.1), all at **Complete Genome** level, each with a current GCF. They have 1–12 replicons (chromosome plus plasmids), made with Autocycler v0.5.2 and annotated with PGAP 6.11 (RefSeq annotation 2026-11-12). CheckM completeness is at least 96.81% and contamination at most 1.79%. No atypical flags. **V**.
- Publication: none found in Europe PMC (2 queries). **NA/NV**, which is to be expected given the release 5 days ago.
- Licence: INSDC data, unrestricted. The Patel paper is a US Government work. **V** (paper text).

### Known issues
- Patel et al. warn that the earlier ECOR assemblies of Messerer et al. 2017 (PLoS One, doi:10.1371/journal.pone.0179880; WGS LY**…) are contaminated in "nearly half" of strains. Table 1 flags 33/72 of them. **Do not use the LY* set.** **V**.
- Patel et al. found ECOR7 and ECOR23 placed in an unexpected phylogroup, which points to strain-identity drift between labs. **V**.
- Within-strain discrepancies between FDA drafts and MSU complete genomes. For ECOR24, 39, 40 and 64 the FDA draft is 0.34–0.53 Mb *larger* than the complete genome. ECOR39 and ECOR40 are also near the top of FDA CheckM contamination (1.08% and ~1%). The two strains may differ (different stock sources: FDA vs. STEC Center), or the drafts may contain extra material. **U**: computed in `B_ecor_samples.tsv`, cause not determined. For path-level truth, use matched reads and assembly from the *same* BioProject.
- **ECOR is a set of isolates, not a single-cell dataset.**

### Minimal subset (2–5 isolates)
ECOR1, 56, 69, 72 (low Illumina volume, few contigs):
- Illumina: SRR3989531, SRR7819142, SRR3989539, SRR7819146, about 0.90 GB FASTQ in total.
- ONT: about 2.6 GB FASTQ in total.
- Complete references: GCA_062083226.1, GCA_062082974.1, GCA_062082961.1, GCA_062082958.1.

---

## 2. GORG-Dark (PRJNA1259050)
- Identity: "Single cell resolved genome composition of prokaryoplankton inhabiting the oceans interior", submitted by Bigelow Laboratory for Ocean Sciences, registered 2025-05-05. The description states 9,698 SAGs from 58 sub-photic marine locations. **V**: `bp_esummary.json`.
- Publication: Chang T, Pachiadaki MG, …, Stepanauskas R. "Single-cell-resolved genome atlas of prokaryoplankton inhabiting the ocean's interior." *Cell* 2026, doi:10.1016/j.cell.2026.08.036, PMID 42743927. Europe PMC lists the licence as CC BY-NC-ND. **V**: `gorg_cell2026_epmc_core.json`. The full text could not be read: cell.com returns a Cloudflare challenge, which was not bypassed, and there is no PMC copy. Paper-level completeness statistics and taxonomy method are therefore **NV**.
- SAG count: **9,698 is exact.** There are 9,698 SRA runs, 9,698 experiments and 9,698 BioSamples, with 1 run per BioSample. **V**: NCBI esearch (`gorg_ncbi_counts.txt`), ENA counts and full run table (`gorg_ena_runs_full.tsv`).
- One SAG = one cell = one library. Each BioSample is one SCGC well ID (e.g. SCGC_AM-210-C02), library_source is "GENOMIC SINGLE CELL", strategy WGA, NextSeq 2000 paired-end. The BioSample text says "single cell isolated from sea water by FACS; single cell amplified by MDA". **V**.
- Amplification: the MDA family with Equiphi29 and phosphorothioate heptamers at 45 °C. Breakdown across assemblies: **WGA-X** 7,566; the same WGA-X recipe without the name 400; **WGA-Y** (ddNTP-modified, for better evenness) 122. **V**: `gorg_assemblies_summary.tsv`.
- Assemblies: **8,088** GenBank assemblies, Contig level, SPAdes 3.9.0, one per BioSample. 1,610 SAGs have reads but no assembly. Only **7** have a RefSeq GCF. 8,086 have PGAP annotation on the GenBank record. **V**.
- Completeness: NCBI CheckM exists for only 13 assemblies (median about 35%, max 67%). Assembly length quartiles are 0.45, 0.69 and 0.99 Mb; contig quartiles are 37, 51 and 74. Typical SAGs are therefore **partial genomes**. The paper's own completeness distribution is **NV**.
- Taxonomy: the NCBI organism names are coarse ("Candidatus Nitrosopelagicus sp." 1,923 runs, Pelagibacteraceae 1,224, …). The paper's GTDB-based assignment is **NV**.
- Volume: **9.17 Tbp**, about **4.57 TB** FASTQ (median 0.94 Gbp per SAG), and 6.47 Gbp of assembled sequence. **V**.
- Known issues: there is **no matched reference genome for any cell**. Completeness is low and variable, and chimerism and contamination are typical of SAGs (see Pachiadaki/Stepanauskas 2024 *Microbiome* on SAG chimerism). Without the paper, contamination is **NV**.

---

## 3. SPAdes ECOLI-SC / ECOLI-MC (Chitsaz et al. 2011)
- Paper: Chitsaz H et al., "Efficient de novo assembly of single-cell bacterial genomes from short-read data sets", *Nat Biotechnol* (2011), doi:10.1038/nbt.1966, PMC3558281. **V**: `spades_chitsaz2011_fulltext.xml` (NCBI efetch db=pmc).
- bioinf.spbau.ru/en/datasets is **still online** (HTTP 200, 2026-11-15). **V**: `spades_bioinf_spbau_datasets.html`. It describes:
  - ECOLI-MC as "E. coli K-12, strain MG1655, standard genomic DNA prepared from culture", the same as UCSD "E. coli reference, lane 6" and ENA ERA000206.
  - ECOLI-SC as "E. coli K-12, strain MG1655, single cell MDA", the same as UCSD "E. coli first single cell MDA, lane 1".
  - The file host spades.bioinf.spbau.ru is **unreachable** (HTTP 000) and has no Wayback snapshot. On the spbau page, both "browse" links point to `.../ECOLI_MC/`, which looks like a page error.
- The UCSD source page (bix.ucsd.edu/projects/singlecell/nbt_data.html) is unreachable live. A Wayback snapshot from 2021-06-30 was read. **V**: `bix_nbt_data_wayback20210630.html`.
  - **ECOLI-MC**: one flow cell lane (lane 6), unamplified gDNA from culture, 2×100 bp, insert 215 ± 11, 28,428,648 reads, 6.50 GB FASTQ (2.07 GB bz2).
  - **ECOLI-SC**: the "first single cell", lane 1. That cell has 4 technical replicate lanes (1–4), and a second cell has 3 lanes (6–8). Lane 1 has 29,124,078 reads, 2×100, insert 267 ± 56, 6.72 GB FASTQ (2.21 GB bz2).
  - Reference given: NC_000913.2 (gi 49175990), 4,639,675 bp. It is now *replaced* by NC_000913.3 (U00096.3). **V**: `spades_ref_nuccore_esummary.json`.
- **ECOLI-MC SRA**: ENA ERA000206 → run ERR008613, study PRJEB2038, sample SAMEA779983. Illumina Cambridge, GA II, flow cell FC30TBBAAXX lane 6, 14,214,324 spots (pairs) × 200 = 2.84 Gbp, SRA size about 1.77 GB. ENA serves only the submitted tar.gz (2.46 GB) with no processed FASTQ; NCBI SRA serves sralite. **V**: `spades_ERA000206_*.tsv`, `spades_ERR008613_sra_runinfo.csv`. The 28.4 M "reads" on the UCSD page equal 2 × 14.2 M spots, which is consistent.
- **ECOLI-SC SRA/ENA**: **no accession found.** The paper gives SRA only for the ERA000206 control, and UCSD lists SRA only for SAR324 (SRA043956). A targeted SRA search (E. coli, MDA or single cell, 2009–2012) found only unrelated Max Planck runs. As far as I can tell, ECOLI-SC exists only on the (now offline) lab servers. Status **NV**, likely **NA**.
- Strain: the paper uses E. coli **ATCC 700926** (= K-12 MG1655) for the single cells. **V** (paper text). The MC control is Illumina's own K-12 MG1655 library, a different lab and stock. **V** (ENA taxon "E. coli str. K-12 substr. MG1655").
- Structure: **neither dataset is a multi-sample pool.** ECOLI-SC is 1 cell → 1 MDA → 1 lane; ECOLI-MC is 1 bulk culture → 1 lane. **V**. The paper reports 94 coverage "blackout" regions (zero coverage) in SC lane 1. **V**.

---

## 4. Better single-cell stress tests with a matched reference (accession-verified)

| Dataset | Accession | Strain / reference | Cells & libraries | Reads | Volume |
|---|---|---|---|---|---|
| **de Bourcy et al. 2014** *PLoS ONE* 9:e105585, doi:10.1371/journal.pone.0105585, CC BY | PRJNA263631 / SRP048908, SAMN02782248–89, SRR1613979–SRR1614020 | Invitrogen **TOP10** (DH10B-derived). The paper maps to K-12 DH10B, i.e. NC_010473.1 / CP000948.1 (4,686,137 bp). *TOP10 ≠ DH10B exactly* (**U**) | 42 libraries: 1 unamplified bulk reference; 19 bulk-DNA WGA dilutions; single cells MALBAC ×5, MDA (microfluidic) ×4, NEB/PicoPLEX ×3; tube MDA "Primary" ×5 plus "Secondary" ×5 (re-amplification of the **same** 5 cells, so not independent). **17 distinct single cells** in total | MiSeq 2×250 | 32.1 Gbp, about 20.6 GB FASTQ |
| **Gole et al. 2013** *Nat Biotechnol* (MIDAS), doi:10.1038/nbt.2720 | PRJNA209527 / SRP026350 | **K-12 MG1655** → NC_000913 | 3 MIDAS single cells (SAMN02213681–83; mates split into separate R1/R2 runs SRR922404–09); 2 in-tube MDA single cells (SAMN02214197/98, SRR923888/923895, GAIIx single-end) | MiSeq or HiSeq 2500 (cell 3), 2×~100 | about 3.0 GB FASTQ |
| **Nishikawa et al. 2015** *PLoS ONE* 10:e0138733 | DRA003579, DRR035999–DRR036007 | K-12 **ATCC 10798** (not MG1655); mapped to NC_000913 | 3 BioSamples: 1 cell droplet-MDA, 1 cell in-tube MDA, 10 cells droplet-MDA; 3 runs each. Whether the 3 runs are separate cells or replicates is **U** | MiSeq 2×300 | about 4.2 GB FASTQ |

All three rows are **V** at ENA/SRA (`item4_*` files). Also screened and not single-cell: PRJNA722381, which is population sequencing (`item4_other_candidates_ena_study.tsv`).

**Recommendation:** de Bourcy 2014 is the best small stress test. It has several independent single cells across three WGA chemistries, a matched unamplified bulk library of the same strain stock, modern 2×250 reads and about 0.5 GB per library. Gole 2013 is the best match if the reference must be exactly MG1655.
