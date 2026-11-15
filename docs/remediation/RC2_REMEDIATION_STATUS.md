# v1.0.1-rc2 Remediation Status

| # | Finding | Status |
|---|---|---|
| F1 | RQ1 240/240 wording | **PASS**: precise wording everywhere; raw 182/240 stated |
| F2 | Spurious-support semantics | **PASS**: exact definitions in evaluator, report, README; column names kept |
| F3 | "path-coherent support" | **PASS**: no occurrences outside historical archives |
| F4 | Candidate table units | **PASS**: labelled as replicate means, 100 planted ORFs per replicate |
| F5 | GCC 14 `-Werror` build | **PASS**: GCC 14.4.0 on Modal, `-Werror` unchanged, no suppression |
| F6 | RSS test portability | **PASS** on macOS and Modal Debian; mutation control fails as required. The ~93 MB-baseline Python of the audit environment was not available (NOT RUN there) |
| F7 | Stale docs | **PASS** |
| F8 | Billing details | **PASS**: removed; archive checker now rejects them |
| F9 | Authorship policy | **PASS**: Ali chose Option B (D-025); rc2 commits already follow it |
| F10 | Internal patch in archive | **PASS**: `export-ignore`; checker rejects it |
| — | Benchmark rerun | **NOT RUN, by design**: no search/timing/data-structure/benchmark-execution change |
| — | R analysis rerun | **NOT RUN**: no analysis change; no local R |
| — | `LICENSE`, `CITATION.cff` | **PASS**: MIT chosen by Ali (D-026) |
| — | GitHub CI | private remote created on Ali's instruction; see `CHANGELOG.md` [1.0.1] for the CI result |
| — | Merge to `main`, tag | done on Ali's instruction (D-027), tag `v1.0.1` |
