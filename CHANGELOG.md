# Changelog

All notable changes. Format: Keep a Changelog; versions follow the charter's release plan.

## [1.0.1] — 2026-11-15 (final)

Final release: rc2 plus the lead's decisions and repository tidy-up, merged into `main`.

### Added
- MIT `LICENSE` and `CITATION.cff` (D-026).
- CI installs GNU `time` and also builds and tests the C++ code with GCC 14 under `-Werror`.

### Changed
- Documentation moved to `docs/` (remediation records in `docs/remediation/`), all linked from the README (D-027).
- Authorship policy: owner identity plus `Co-Authored-By` trailers (D-025); specification credit confirmed (D-022).
- All development branches merged into `main` and removed; history kept, releases tagged.

## [1.0.1-rc2] — 2026-11-15

### Fixed
- C++ CLI builds with GCC 14 under `-Werror` (typed array instead of an initializer list of temporaries).
- RSS tests are baseline-relative; no fixed Python memory ceiling.
- RQ1 reporting: precise criterion wording (240/240 within criterion, 182/240 raw), exact metric definitions, replicate-mean labels.
- Documentation reconciled; account-level billing details removed; internal patches excluded from archives.

### Added
- Required-flag CLI tests; Modal GCC 14 and Linux RSS checks; stricter release-archive checker.

## [1.0.1-rc1] — 2026-11-15

### Fixed
- Equivalent timing phases (new `canonicalize`), strict-then-permissive in all implementations (D-019).
- Peak RSS measured through `/usr/bin/time`; v1.0.0 Modal floor was fork inheritance (D-020).
- RQ1: explicit true-observation and spurious-colour processes, true-sample evaluation, 10 paired replicates (D-021).

### Added
- Timing-contract, RQ1-model, RSS and release-archive tests; verified prior-art review; remediation documents.

### Superseded
- v1.0.0 search speed-ups, Modal memory figures and RQ1 results (kept, labelled).

## [1.0.0] — 2026-11-14

Tagged release; see below.

## [0.2.0] — 2026-11-14

### Added
- Algorithm specification v1.0, I/O schema v1.0, architecture, test plan, decision log.
- 39 conformance cases (10 functional scenarios + G11 frame-shifting loop, 13 boundary,
  15 invalid-input) with hand-derived expectations, brute-force oracle, fixture consistency check.
- Python (reference), C++17 and Rust implementations; each passes 39/39 conformance and its own
  unit tests. The three are byte-identical on all 20 generated workloads.
- Seeded workload generator (perf grid + extension sizes, cycle-heavy stress, RQ1 dropout
  sweep), cross-language validator, RQ1 evaluator, benchmark runner, Modal app, base-R analysis.
- AI usage ledger, CI workflow and Makefile.

### Fixed
- Fixture expectations B09 (`max_depth`) and B10 (trailing-`A` start frame), reported by the
  implementations (D-014).
- Stress generator could create `ATGATG` (an in-frame `TGA`); insertions are now ≥ 4 bases apart.

### Known issues
- Commit `77d63d3` ("feat: add AI agent usage ledger") also contains `analysis/analysis.R` and
  `references.bib`, which were staged by mistake; the content is correct, only the commit is
  not atomic. History was not rewritten.

## [0.1.0]
Not tagged separately: the first working prototype and the three-language milestone were
reached on the same day, so the release goes straight to 0.2.0.
