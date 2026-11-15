# AI Usage and Attribution

**Status:** Complete for v1 development (2026-11-14).

This is the authoritative record of who did what. Under D-001, Git commits use the project
lead's identity and contain no tool or model names, so this file, not `git log`, shows AI
involvement.

## Roles

| Contributor | Contribution |
|---|---|
| **Ali Mohammadi** (project lead) | Research direction and questions (RQ1–RQ4), the idea of frame-aware candidate path search with colour-support policies, three-language comparison and AI-effort measurement, Algorithm specification , the detailed charter, choice of Modal/TDD/Git practices, supervision of the agents, and final responsibility for all content. |
| Claude Opus 5.5 (coordinating development agent, high effort) | I/O schema; fixture design with hand-derived expectations; brute-force oracle; conformance and cross-language runners; workload generator; benchmark runner; Modal app; R analysis; code review; integration; all documentation. |
| Claude Sonnet 5.5 (implementation agents) | Python, C++17 and Rust implementations and their unit tests. |
| Claude Haiku 5.5 (supporting agents) | Makefile and CI workflow; Crossref verification of bibliographic metadata. |

No code in this repository was written by hand by Ali. His contribution is the research design,
direction, review and decisions. That is the point of the AI-assisted engineering part of the
study (RQ4).

## Commit → producing agent

| Commit | Message | Produced by |
|---|---|---|
| 5f83c6b | chore: initialise repository with security baseline | Opus |
| e14b161 | docs: add project charter, architecture, algorithm spec and I/O schema | Opus |
| c04f7b4 | test: add hand-derived fixtures, brute-force oracle and conformance runner | Opus |
| ba3b690 | docs: specify numeric field ranges and usage-error contract | Opus |
| c4c6b85 | ci: add Makefile targets and GitHub Actions workflow | Haiku (CI agent) |
| 196868e | test: add Python unit tests for traversal and validation | Sonnet wrote the tests; Opus committed them after the agent was cut off (one obfuscated assertion simplified) |
| 862e319 | test: add C++ unit tests for traversal and validation | Sonnet (C++ agent) |
| a8c8606 | feat: implement Python reference traversal | Sonnet (Python agent) |
| 859025c | feat: implement C++17 candidate search | Sonnet (C++ agent) |
| e3268e3 | test: correct hand-derived counters for B09 and B10 | Opus, after both implementation agents reported the error |
| a0ad4f0 | test: add Rust unit tests for traversal and validation | Sonnet (Rust agent) |
| 5533352 | feat: add seeded workload generator, cross-language check, RQ1 evaluator, benchmark runner and Modal app | Opus |
| 2bd8c27 | feat: implement Rust bounded traversal | Sonnet (Rust agent) |
| 77d63d3 | feat: add AI agent usage ledger | Opus (also accidentally contains `analysis/analysis.R` and `references.bib`; see CHANGELOG) |
| later | documentation, results, report | Opus |

Merge commits were made by Opus after review.

## Notable events

- **Fixture errors caught by implementations.** Two of the hand-derived summary expectations
  were wrong (B09 `max_depth`, B10 trailing-`A` start frame). The Python and C++ agents each
  stopped and reported the disagreement instead of editing fixtures, as instructed. The fix was
  verified by hand and recorded (D-014). Candidate expectations were correct throughout; they had
  been cross-checked by the oracle.
- **Generator defect caught by review.** Stress workloads were meant to be stop-free, but
  adjacent `ATG` insertions created `TGA`. This was noticed because the stress run produced
  candidates; it was fixed before any benchmark.
- **API interruptions.** All Sonnet agents and the literature agent hit the account's spend limit
  (HTTP 429) on their first leg, and the Rust agent later hit a network error. Each was resumed
  with its saved context. Usage of interrupted legs was not exposed.
- **Review notes** for the lead: see `LIMITATIONS.md` items 9–10.
