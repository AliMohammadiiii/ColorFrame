# Evidence (metadata only, retrieved 2026-11-15)

Primary-source metadata behind the feasibility package. No read or genome data is stored here.

| File | Content | Source |
|---|---|---|
| `A_mock_communities_findings.md` | Zymo D6300, MBARC-26, BMock12, HiFi MSA-1003: libraries, accessions, references, licences, verdicts | ENA Portal API, NCBI SRA/Assembly/Datasets, Europe PMC full text |
| `B_isolates_single_cell_findings.md` | ECOR, GORG-Dark, SPAdes ECOLI-SC/MC, de Bourcy 2014, Gole 2013, Nishikawa 2015 | NCBI E-utilities, ENA, Europe PMC, archive.org snapshot of the original SPAdes data page |
| `C_simulation_prior_art_findings.md` | CAMISIM, CAMI II toy HMP, Raphenya AMR, ggCaller manuscript data, Bifrost colour/orientation model (from code), Pyrodigal, ggCaller | GitHub (read-only), Zenodo, CAMI portal, Europe PMC |
| `ecor_samples.tsv` | One row per ECOR isolate: FDA Illumina BioSample/runs/draft assembly beside the ONT complete genome | NCBI SRA runinfo, NCBI Datasets, ENA |
| `ecor_pilot_runs.tsv` | ENA file report for the 4 pilot runs (URLs, bytes, MD5) | ENA Portal API |
| `debourcy_runs.tsv` | ENA file report for all 42 de Bourcy libraries | ENA Portal API |
| `cami_uro_abundance_overlap.tsv` | Genomes present per CAMI II toy urogenital sample and overlap with sample 6 | CAMI Swift `abundance*.tsv` |

Independent spot checks by the coordinating agent (2026-11-15):
- PRJNA1543032 has 72 assemblies, all Complete Genome (ECOR01 = GCF_062083226.1);
- PRJNA230969 is a US FDA *E. coli* project with 1,705 BioSamples;
- PRJNA263631 has 42 runs and 32.1 Gbp;
- PRJEB29504 has 10 per-isolate Illumina libraries;
- PRJNA324704 has 2 mixed runs;
- the HiFi mock is one mixed BioSample;
- the CAMI urogenital sample 6 has 24 genomes present.
