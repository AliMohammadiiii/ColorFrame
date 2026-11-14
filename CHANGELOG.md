# Changelog

All notable changes. Format: Keep a Changelog; versions follow the charter's release plan.

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
