# A: Mock-community dataset verification (metadata only; no read files downloaded)

Checked on 2026-11-15. Evidence files are in this directory. Status labels: **V** = Verified at the primary source, **PV** = Partially verified, **NV** = Not verified, **NA** = Not available, **U** = Unclear.

Primary endpoints used:
- Europe PMC search/fullTextXML/supplementaryFiles: `https://www.ebi.ac.uk/europepmc/webservices/rest/...`
- ENA filereport: `https://www.ebi.ac.uk/ena/portal/api/filereport?accession=<acc>&result=read_run&fields=...`
- NCBI SRA runinfo: `https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=<acc>`
- NCBI E-utilities (esearch, elink, esummary): `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- NCBI Datasets v2: `https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/<accs>/dataset_report`
- GigaDB API: `https://gigadb.org/api/dataset/?doi=100580`
- Springer ESM for BMock12 supplement: `https://static-content.springer.com/esm/art%3A10.1038%2Fs41597-019-0287-z/MediaObjects/41597_2019_287_MOESM2_ESM.docx`

---

## 1. ZymoBIOMICS 10-species mock (Nicholls et al. 2019)

- **Publication (V):** Nicholls SM, Quick JC, Tang S, Loman NJ. *GigaScience* 2019, doi 10.1093/gigascience/giz043, PMC6520541, CC BY 4.0. Protocol doi 10.17504/protocols.io.x9tfr6n resolves to protocols.io (V). Evidence: `epmc_search_10_1093_gigascience_giz043.json`, `fulltext_zymo_nicholls2019_PMC6520541.{xml,txt}`, `doi_resolution_check.txt`.
- **Communities (V):** D6300 Even, lot ZRC190633. D6310 Log, lot ZRC190842. 8 bacteria and 2 yeasts. The paper notes that the S. enterica strain listed as LT2 is "likely to be Serotype Choleraesuis", so it may be mis-annotated.
- **Project (V):** ENA **PRJEB29504** (ERP111811), 26 runs. Evidence: `ena_read_run_zymo_PRJEB29504.tsv`.

### Libraries in PRJEB29504
**Per-isolate (V; paper Table 1 matches ENA):** 10 Illumina HiSeq 1500 WGS runs, one isolate and BioSample per run, made from pure cultures:

| Run | Organism | BioSample | bases | fastq_bytes |
|---|---|---|---|---|
| ERR2935848 | Salmonella enterica | SAMEA5138295 | 2,882,486,470 | 1,838,398,294 |
| ERR2935849 | Staphylococcus aureus | SAMEA5138296 | 3,472,150,124 | 2,008,426,137 |
| ERR2935850 | Enterococcus faecalis | SAMEA5138297 | 3,811,843,222 | 2,263,399,058 |
| ERR2935851 | Bacillus subtilis | SAMEA5138298 | 4,679,172,440 | 3,075,998,552 |
| ERR2935852 | Escherichia coli | SAMEA5138299 | 1,434,007,090 | 884,142,163 |
| ERR2935853 | Pseudomonas aeruginosa | SAMEA5138300 | 1,492,159,456 | 950,598,088 |
| ERR2935854 | Listeria monocytogenes | SAMEA5138301 | 2,133,936,686 | 1,273,151,750 |
| ERR2935855 | Saccharomyces cerevisiae | SAMEA5138302 | 2,412,887,778 | 1,460,030,993 |
| ERR2935856 | Cryptococcus neoformans | SAMEA5138303 | 1,701,262,786 | 1,054,152,591 |
| ERR2935857 | Limosilactobacillus fermentum | SAMEA5138304 | 3,308,636,780 | 2,174,040,595 |

Totals: 27.33 Gbases and 16.98 GB fastq. The 8 bacteria alone come to 14.47 GB.

**Mixed community (V):** 16 runs on 2 Even BioSamples (SAMEA5065621 and SAMEA5157164) and 2 Log BioSamples (SAMEA5065622 and SAMEA5138305).
- Illumina: ERR2984773 (Even, MiSeq, 2.65 Gb) and ERR2935805 (Log, HiSeq 1500, 9.66 Gb).
- ONT FASTQ listed in paper Table 2: ERR3152364 (Even GridION), ERR3152365 (Even PromethION), ERR3152366 (Log GridION), ERR3152367 (Log PromethION).
- ONT signal runs listed in the paper: ERR2887847–52. ENA shows base_count 0 for these and gives only submitted_bytes. Their total is about 4.4 TB, which matches the paper's "4.2 TB" approximately.
- ENA also lists ERR2906227–30 (ONT FASTQ on the same samples). The paper does not cite these runs, so their relation to ERR3152364–67 is **U** (they may be an earlier basecall).
- ENA has base_count 0 for ERR3152367 but fastq_bytes of 160 GB. This is a metadata gap.
- Volume: all FASTQ in PRJEB29504 totals 700.2 GB. Submitted files including signal total 5.12 TB.

### Related per-isolate data cited by Nicholls Table 1 (from McIntyre et al. 2019, Nat Commun)
- NCBI **PRJNA477598** has 79 runs (V; `ena_read_run_zymo_pacbio_mcintyre_PRJNA477598.tsv`).
- It holds per-isolate PacBio RSII/Sequel, ONT GridION and Illumina WGS runs, plus bisulfite and MeDIP runs, for the 10 Zymo strains on BioSamples SAMN09475310–19.
- It also has 9 runs of an unrelated E. coli K-12 sample (SAMN10365290) that should be excluded.
- WGS per-isolate volumes:
  - PacBio: 17 runs, 17.6 GB fastq, for 8 strains. No PacBio for L. fermentum or C. neoformans.
  - ONT: 11 runs, 9.6 GB.
  - Illumina: 22 runs, 17.9 GB.
- Run lists are in the evidence file.

### Reference assemblies (V via NCBI Datasets; `ncbi_assembly_search_zymo.json`, `ncbi_datasets_zymo_PRJNA477598_assemblies.json`)
All are from PRJNA477598 (Weill Cornell), not from Nicholls.

| Strain | Assembly | Level / contigs | Annotation |
|---|---|---|---|
| B. subtilis NRS 231 | GCA_005153965.1 | Chromosome / 2 | PGAP (GenBank); RefSeq GCF suppressed |
| E. coli NRRL B-1109 | GCA_005153645.1 | Chromosome / 2 | PGAP (GenBank); RefSeq GCF suppressed |
| E. faecalis 110 | GCF_005154485.1 | Chromosome / 1 | RefSeq |
| L. fermentum B1 28 | GCF_005341425.1 | Chromosome / 1 | RefSeq |
| L. monocytogenes Li 2108 | GCF_005154665.1 | Chromosome / 1 | RefSeq |
| P. aeruginosa PRD-10 | GCF_005154325.1 | Chromosome / 1 | RefSeq |
| S. enterica Typhimurium NRRL B-4212 | GCF_005154105.1 | Chromosome / 2 | RefSeq |
| S. aureus NRRL B-41012 | GCF_005153985.1 | Chromosome / 2 | RefSeq |
| S. cerevisiae NRRL Y-567 | GCA_007556415.1 | Contig / 51 | **none** |
| C. neoformans×deneoformans CBS 132 | GCA_006992865.1 | Contig / 559 | **none** |

- That these BioSamples are the same physical Zymo strains is **PV**. Nicholls Table 1 cites them as the PacBio data for the Zymo organisms, but the strain designations differ in style (for example NRS 231 vs NRRL B-354).
- Nicholls deposited an Illumina SPAdes per-isolate assembly, `Zymo-Isolates-SPAdes-Illumina.fasta` (71.4 MB), and ONT metagenome assemblies on GigaDB 10.5524/100580. No NCBI/ENA assembly exists under PRJEB29504 (ENA query returned none). GigaDB licence: **CC0 1.0** (V; `gigadb_100580_dataset.json`, `gigadb_100580_readme.txt`). GitHub code is MIT.

### Assessment
- Licence (V): paper and supporting data CC BY 4.0; GigaDB CC0.
- Known issues (V, as stated by authors): possible S. enterica serotype mis-annotation; L. monocytogenes assembled poorly in the Log community despite the highest coverage; the C. neoformans strain is a diploid cross, so its assemblies are larger.
- **(A) Sample-resolved: YES (V).** There are 10 per-isolate Illumina libraries with their own run accessions, plus per-isolate PacBio, ONT and Illumina in PRJNA477598. The ONT data itself is mixed-community only.
- **(B) Gene-level truth: YES for 8 bacteria (V)** through RefSeq/PGAP annotation of the PRJNA477598 assemblies. Yeasts have no annotation.
- **(C) Path-level: YES for 8 bacteria** using closed or near-closed per-strain assemblies (1–2 contigs) and per-isolate long reads. Yeasts are fragmented (contig level).

---

## 2. MBARC-26 (Singer et al. 2016)

- **Publication (V):** *Sci Data* 3:160081, doi 10.1038/sdata.2016.81, PMC5037974, CC BY 4.0. Metadata is CC0. 23 bacteria and 3 archaea. Illumina HiSeq 2000 (2x150) and PacBio RS II (P4C2). Evidence: `fulltext_mbarc26_singer2016_PMC5037974.{xml,txt}`.
- **Project (V):** NCBI **PRJNA324704** (SRP076357), 2 runs, both mixed (`ena_read_run_mbarc26_PRJNA324704.tsv`, `ncbi_runinfo_mbarc26_PRJNA324704.csv`):

| Run | Exp | BioSample | Platform | reads/spots | bases | fastq_bytes | SRA size |
|---|---|---|---|---|---|---|---|
| SRR3656745 | SRX1836716 | SAMN05213576 | Illumina HiSeq 2000 | 173,981,994 pairs | 51,903,119,854 | 41,541,162,753 | 32,698 MB |
| SRR3656744 | SRX1836715 | SAMN05213577 | PacBio RS II | 53,654 | 55,855,781 | 45,130,344 | 36 MB |

- Paper and repository agree: 347,963,988 filtered Illumina reads = 2 × 173,981,994, and 53,654 filtered PacBio reads. The deposited data is **filtered** reads, not raw.
- Per-isolate libraries within the dataset: **NONE (V).**

### References (V; `ncbi_mbarc26_nuccore_to_assembly.json`, `ncbi_datasets_mbarc26_GCF_reports.json`)
Paper Table 1 accession → assembly. All are Complete Genome with RefSeq annotation unless noted.

| Organism | Paper accession | Assembly |
|---|---|---|
| T. roseus | NC_018014 | GCF_000265425.1 |
| C. glutamicum | NC_003450 | GCF_000011325.1 |
| N. dassonvillei | NC_014211 | GCF_000092985.1 |
| O. uli | NC_014363 | GCF_000143845.1 |
| S. rotundus | NC_014168 | GCF_000092825.1 |
| E. vietnamensis | NC_019904 | GCF_000325705.1 |
| M. silvanus | NC_014212 | GCF_000092125.1 |
| C. perfringens | NC_008261 | GCF_000013285.1 |
| C. thermocellus | NC_009012 | GCF_000015865.1 |
| D. acidiphilus | NC_018068 | GCF_000255115.2 |
| D. meridiei | NC_018515 | GCF_000231385.2 |
| D. gibsoniae | NC_021184 | GCF_000233715.2 |
| S. pyogenes | NC_002737 | GCF_000006785.2 |
| T. composti | NC_019897 | GCF_000227705.2 |
| E. coli MG1655 | NC_000913 | GCF_000005845.2 |
| F. aurantia | NC_017033 | GCF_000242255.2 |
| H. baltica | NC_012982 | GCF_000023785.1 |
| P. stutzeri | NC_019936 | GCF_000327065.1 |
| S. bongori | NC_015761 | GCF_000252995.1 |
| S. enterica arizonae RSK2980 | NC_010067 | GCA_000018625.1 (see note) |
| S. smaragdinae | NC_014364 | GCF_000143985.1 |
| F. pennivorans | NC_017095 | GCF_000235405.2 |
| C. akajimensis | NC_014008 | GCF_000025905.1 |
| Halovivax ruber | CP003050.1 | GCF_000328525.1 |
| N. gregoryi | NC_019792.1 | GCF_000230715.2 |
| N. occultus | NC_019974.1 | GCF_000328685.1 |

- **S. enterica arizonae note:** NC_010067.1 and GCF_000018625.1 are **suppressed** in RefSeq. GCA_000018625.1 is current and has submitter annotation.
- These are the strains' **published finished genomes**. They were not sequenced from the mock DNA. Lengths differ slightly from paper Table 1 for E. coli (current 4,641,652 vs 4,639,675 in the paper) and S. pyogenes (1,852,433 vs 1,852,441), because RefSeq versions changed.

### Archival per-strain reads (outside the MBARC-26 dataset)
Original genome-project reads exist on 17 of 26 strain BioSamples. They are mostly Illumina GAII/HiSeq or 454 from the original JGI projects. Some BioSamples also carry runs from unrelated studies, for example A. thermocellus with 44 HiSeq runs (PRJNA206991) and E. coli MG1655 with NovaSeq/Sequel runs. 9 BioSamples have no runs. These were neither generated nor described by Singer et al. (V; `ena_isolate_biosample_runs_bmock12_mbarc26.tsv`).

### Assessment
- Known issues (V, as stated by authors): T. composti is over-represented relative to molarity, "likely due to contamination", and is a known lab contaminant. Platform-specific GC and amplification bias.
- **(A) Sample-resolved: NO (V)** within the dataset: one mixed sample, two platforms. Per-strain reads exist only as heterogeneous legacy deposits.
- **(B) Gene-level: YES (V).** RefSeq-annotated finished genomes for 25/26; arizonae annotation is GenBank-only.
- **(C) Path-level: reference-level only.** Finished genomes of the same strains are available, but no per-strain read set comes from the mock material.

---

## 3. BMock12 (Sevim et al. 2019)

- **Publication (V):** *Sci Data* 6:285, doi 10.1038/s41597-019-0287-z, PMC6879543, CC BY 4.0. Metadata is CC0. Evidence: `fulltext_bmock12_sevim2019_PMC6879543.{xml,txt}`, `bmock12_supplementary_tables_MOESM2.txt`.
- **Project (V):** NCBI **PRJNA496047** (SRP166033). One BioSample, **SAMN10236717** (synthetic metagenome, Gp0334079). 5 runs, all mixed (`ena_read_run_bmock12_PRJNA496047.tsv`, `ncbi_runinfo_bmock12_PRJNA496047.csv`):

| Run | Exp | Platform | reads/spots | bases | fastq_bytes |
|---|---|---|---|---|---|
| SRR8073716 | SRX4901583 | Illumina HiSeq 2500 | 213,367,823 pairs | 64,437,082,546 | 42,265,393,819 |
| SRR8073715 | SRX4901584 | PacBio RS II | 165,088 | 1,084,835,852 | 939,609,587 |
| SRR8073714 | SRX4901585 | PacBio RS II | 224,718 | 1,498,501,396 | 1,314,527,883 |
| SRR8073713 | SRX4901586 | ONT MinION (10 kb size selection) | 187,507 | 3,737,495,058 | 3,616,756,404 |
| SRR8351023 | SRX5161985 | ONT MinION (no size selection) | 144,976 | 924,061,018 | 929,604,996 |

- Total: about 49.07 GB fastq.
- Paper vs repository:
  - Illumina: Table 2 lists 426,735,646 raw / 422,896,888 filtered reads. SRA has 2 × 213,367,823 = 426,735,646, so the deposit is **raw** reads.
  - PacBio: the two runs sum to 389,806, which matches the paper.
  - ONT: SRR8073713 has 187,507 reads, which matches. SRR8351023 is not in Table 2.
- Metagenome co-assemblies (V): GCA_003957615.1 (PacBio+Illumina, 2,951 contigs, PRJNA505201), GCA_003957625.1 (ONT+Illumina, 2,714 contigs, PRJNA505202), GCA_003957645.1 (Illumina only, 4,038 contigs). None is annotated or binned per strain in NCBI.

### Strain references
The paper used IMG drafts, by IMG taxon ID, downloaded 2017-06-27. NCBI equivalents are below (V; `ncbi_assembly_search_bmock12*.json`, `ncbi_datasets_bmock12_and_misc_reports.json`):

| Strain | IMG ID | NCBI assembly | Contigs | Annotation |
|---|---|---|---|---|
| Muricauda (Allomuricauda) sp. ES.050 | 2615840527 | **none found** | — | — |
| Thioclava sp. ES.032 | 2615840533 | **none found** | — | — |
| Cohaesibacter sp. ES.047 | 2615840601 | GCF_900215505.1 | 1 | RefSeq |
| Propionibacteriaceae bact. ES.041 | 2615840646 | GCA_002563805.1 | 1 | JGI annotation; RefSeq GCF suppressed |
| Marinobacter sp. LV10R510-8 | 2615840697 | **none found** | — | — |
| Marinobacter sp. LV10MA510-1 | 2616644829 | GCF_002563885.1 | 1 | RefSeq |
| Psychrobacter sp. LV10R520-6 | 2617270709 | GCF_900182925.1 | 1 | RefSeq |
| M. echinaurantiaca DSM 43904 | 2623620557 | GCF_900090235.1 | 1 | RefSeq |
| M. echinofusca DSM 43913 | 2623620567 | GCF_900091445.1 | 1 | RefSeq |
| M. coxensis DSM 45161 | 2623620609 | GCF_900090295.1 | 1 | RefSeq |
| Halomonas sp. HL-4 | 2623620617 | GCF_900215475.1 | 1 | RefSeq |
| Halomonas sp. HL-93 | 2623620618 | GCF_900086985.1 | 1 | RefSeq; also PNNL GCA_001314745.1 |

- "None found" means no NCBI Assembly was found by organism or taxid search. These three references are available only in IMG (NV in NCBI).
- Several NCBI lengths are exactly 100 bp longer than the IMG lengths in supplementary Table S1 (U).

### Per-isolate reads (V; `ena_isolate_biosample_runs_bmock12_mbarc26.tsv`)
These are **not part of the BMock12 deposit**. They are the JGI isolate-genome PacBio RS projects for all 12 strains:

| Strain | BioSample | Runs | fastq_bytes |
|---|---|---|---|
| ES.050 | SAMN04515606 | SRR4156293, SRR4156294, SRR4156295 | 0.47 GB |
| ES.032 | SAMN04515646 | SRR4125771, SRR4125772 | 0.43 GB |
| ES.047 | SAMN04515647 | SRR4156301, SRR4156302 | 0.51 GB |
| ES.041 | SAMN06298213 | SRR5271177, SRR5271178 | 0.49 GB |
| LV10R510-8 | SAMN04488488 | SRR4167810, SRR4167811 | 0.67 GB |
| LV10MA510-1 | SAMN04488489 | SRR4167812, SRR4167813 | 0.59 GB |
| LV10R520-6 | SAMN04488491 | SRR4167799, SRR4167800 | 0.77 GB |
| M. echinaurantiaca | SAMN04488338 | SRR4164055, SRR4164056, SRR4164057 | 3.18 GB |
| M. echinofusca | SAMN04488339 | SRR4164074, SRR4164075, SRR4164076 | 3.39 GB |
| M. coxensis | SAMN04488465 | SRR4164085, SRR4164086, SRR4164087 | 3.30 GB |
| HL-4 | SAMN04488142 | SRR4171275, SRR4171276 | 0.52 GB |
| HL-93 | SAMN04488143 | SRR4171290, SRR4171291 | 0.51 GB |

Total: about 14.8 GB. The two Halomonas strains alone come to 1.03 GB.

### Assessment
- Known issues (V, as stated by authors):
  - The two Halomonas strains share **99% ANI** (Mash distance 0.01) and cause many hybrid misassemblies. The Marinobacter pair shares 85% ANI.
  - The three Micromonospora are high-GC with high ANI.
  - **M. coxensis is effectively absent**: its reads were "negligible", for example 18,442 Illumina reads, and it was dropped from Table 3. The data effectively represents 11 strains, not 12.
  - Size selection biases ONT read lengths.
- **(A) Sample-resolved: NO within the dataset (V).** One BioSample, all mixed. Per-strain PacBio RS from the original isolate projects exists separately, but it does not come from the mock aliquot.
- **(B) Gene-level: PARTIAL.** NCBI-annotated single-contig assemblies exist for 9/12. The other 3 are IMG only.
- **(C) Path-level: reference-level for 9/12.** The isolate PacBio RS reads (about 85–87% accuracy) allow per-strain read support.

---

## 4. "PacBio HiFi 20-microbe mock" (Hon et al. 2020)

- **Publication (V):** Hon T et al. *Sci Data* 2020, doi 10.1038/s41597-020-00743-4, PMC7673114, CC BY 4.0. The paper states the data "can be used without restriction".
- **Does it contain a 20-microbe mock? YES (V).** It is **ATCC MSA-1003** (20 bacteria, staggered 0.02–18%), **not** ZymoBIOMICS D6331. The secondary report's citation is correct for the paper, but if it named D6331 or the Zymo gut standard, that is wrong.
- **Project (V):** SRA study **SRP258341** = BioProject **PRJNA627939**. Mock BioSample **SAMN14691545** (synthetic metagenome). Evidence: `ena_read_run_hifi_hon2020_SRP258341.tsv`, `ncbi_runinfo_hifi_hon2020_SRP258341.csv`, `hon2020_supplementary_MOESM1.txt`, `supp_hon2020/`.

| Run | Type | reads | bases | fastq_bytes | SRA size |
|---|---|---|---|---|---|
| SRR11606871 | HiFi CCS, mixed (2 SMRT Cells 8M) | 5,646,628 | 59,145,712,992 | 44,945,102,446 | 36,448 MB |
| SRR12371719 | raw subreads, mixed | 57,005,189 | 507,041,536,716 | 155,590,929,084 | 122,081 MB |
| SRR12358170 | raw subreads, mixed | 57,269,742 | 511,610,523,859 | 156,640,493,193 | 123,179 MB |

- Paper Table 3 (5.6 M reads, 59.1 Gb, mean 10.5 kb, RQ 35) matches SRR11606871.
- **No per-strain libraries (V).**

### References (paper Supplementary Table 1, V)
These are public GenBank reference-strain genomes. They were not sequenced from the mock. Resolved assemblies are in `ncbi_atcc_msa1003_nuccore_to_assembly.json` and `ncbi_datasets_atcc_msa1003_refs.json`:

| Organism | Strain | Abundance | Accession → assembly | Notes |
|---|---|---|---|---|
| A. baumannii | ATCC 17978 | 0.18% | CP000521 → GCF_000015425.1 | RefSeq suppressed |
| B. cereus | ATCC 10987 | 1.8% | AE017194 → GCF_000008005.1 | suppressed |
| B. vulgatus | ATCC 8482 | 0.02% | CP000139 → GCF_000012825.1 | |
| B. adolescentis | ATCC 15703 | 0.02% | AP009256 → GCF_000010425.1 | |
| C. beijerinckii | ATCC 35702 | 1.8% | NZ_CP006777 → GCF_000767745.1 | |
| C. acnes | ATCC 11828 | 0.18% | CP003084 → GCF_000231215.1 | |
| D. radiodurans | ATCC BAA-816 | 0.02% | AE000513 + plasmids → GCF_000008565.1 | |
| E. faecalis | ATCC 47077 | 0.02% | NC_017316 → GCF_000172575.2 | OG1RF |
| E. coli | ATCC 700926 | 18% | U00096 → GCF_000005845.2 | |
| H. pylori | ATCC 700392 | 0.18% | AE000511 → GCF_000008525.1 | suppressed |
| L. gasseri | ATCC 33323 | 0.18% | CP000413 → GCF_000014425.1 | |
| N. meningitidis | ATCC BAA-335 | 0.18% | AE002098 → GCF_000008805.1 | |
| P. gingivalis | ATCC 33277 | 18% | AP009380 → GCF_000010505.1 | |
| P. aeruginosa | ATCC 9027 | 1.8% | PDLX01000000 → GCF_002563335.1 | contig-level; now "P. paraeruginosa" |
| R. sphaeroides | ATCC 17029 | 18% | CP000577 → GCF_000015985.1 | |
| S. odontolytica | ATCC 17982 | 0.02% | DS264586/5 → GCF_000154225.1 | scaffold |
| S. aureus | ATCC BAA-1556 | 1.8% | CP000255 → GCF_000013465.1 | |
| S. epidermidis | ATCC 12228 | 18% | AE015929 → GCF_000007645.1 | |
| S. agalactiae | ATCC BAA-611 | 1.8% | AE009948 → GCF_000007265.1 | |
| S. mutans | ATCC 700610 | 18% | AE014133 → GCF_000007465.2 | |

- Supplementary Table 1 has an "18..0%" typo.
- That each ATCC number corresponds to the named reference strain (for example ATCC 700926 = MG1655) is **PV**: NCBI strain names were not cross-checked against the ATCC catalogue.
- Known issues (V, as stated by authors): coverage spans about 3 to 5,000-fold; the authors report 98.9% of reads mapped to the reference set; 900-fold abundance range.

### Separate D6331 HiFi dataset (not part of Hon et al.)
ZymoBIOMICS D6331 PacBio HiFi data exists separately as **PRJNA680590**, "Sequencing of ZymoBIOMICS Gut Microbiome Standard D6331: PacBio HiFi Data from Sequel II System". It has one BioSample, SAMN16885726 (mixed), and 3 runs: SRR13128014 (STD, 17.99 Gb), SRR13128013 (LOW, 25.78 Gb) and SRR13128012 (ULI, 21.33 Gb) (V; `ena_read_run_zymoD6331_hifi_PRJNA680590.tsv`). The associated publication was **NV**.

### Assessment
- **(A) Sample-resolved: NO (V).**
- **(B) Gene-level: YES (V)** through current RefSeq annotation for 17 of 20 references. Three are RefSeq-suppressed and need the GenBank GCA. The references are canonical strain genomes, not lot-specific.
- **(C) Path-level: reference-level only.** The HiFi reads are mixed, so assignment to a strain needs mapping.
