# AI Usage and Attribution

**Status:** Final for v1.0.1 (2026-11-15).

This is the authoritative record of who did what. All commits use the project lead's Git
identity (D-001), so the author field of a commit does **not** identify the agent that produced
it; this file does. Commits up to rc1 (`44fbbf3`) carry no model names. The rc2 commits carry a
`Co-Authored-By: Claude Opus 5.5` trailer, which departs from D-001; the policy for future work
is Option B, decided by the lead (D-025, below).

**Contribution statement.** The implementation code in this repository was produced by AI agents.
Ali supplied the research direction and the algorithm design brief, directed the work and its
remediation, commissioned the independent reviews, and owns the final scientific decisions and
interpretation. *(Adapted from the audit's suggested sentence: the records show direction and
commissioned review, but no line-level code review by Ali, so "reviewed the work" is not claimed.)*

## Roles (reconciled in v1.0.1 from the recorded prompts, commits and decision log)

| Contributor | Contribution that the records substantiate |
|---|---|
| **Ali Mohammadi** (project lead) | Original project idea and research direction; research questions RQ1–RQ4; the intended comparisons (strict vs permissive support, Python/C++/Rust, AI-assisted effort); scope; **the algorithm design brief** in the charter he wrote (graph model, data-contract columns, traversal state, 13-step core algorithm, search limits, both support policies, the ten fixture scenarios, workload sizes/branching/seed, benchmark protocol, token-ledger columns); the decision to commission the independent review and this remediation; final scientific decisions and interpretation. |
| **Collaborative** | **Algorithm specification.** Ali's design brief (above) defined the algorithm. Opus turned it into the formal, normative `ALGORITHM_SPEC.md` (pseudocode, start-position ownership, uniform overlap, counter definitions, exploration order) and `INPUT_OUTPUT_SCHEMA.md` (formats, validation order, error codes). No explicit review of the formal text by Ali is recorded. |
| Claude Opus 5.5 (coordinating development agent, high effort) | Formal spec and schema as above; fixture contents with hand-derived expectations (including the two errors later corrected, D-014); brute-force oracle; conformance, cross-language, timing-contract, RQ1 and RSS test harnesses; workload generator; benchmark runner; Modal app; R analysis; code review; integration; documentation. **v1.0.1:** all remediation code and docs, including the timing-phase changes in the Python, C++ and Rust implementations (done directly rather than delegated, D-023). **rc2:** RQ1 wording, C++ GCC 14 fix, RSS tests, GCC 14 and RSS Modal checks, documentation, release check (also not delegated). |
| Claude Sonnet 5.5 (implementation agents) | v1.0.0 Python, C++17 and Rust implementations and their unit tests. |
| Claude Haiku 5.5 (supporting agents) | Makefile and CI workflow; Crossref verification of bibliographic metadata (v1.0.0). |

No code in this repository was written by hand by Ali.

**Record of the lead's edit.** On 2026-11-14/15 Ali edited this table to move "Algorithm
specification" from Opus to himself (preserved as commit `3aa59a0` and, in the development
repository only, as `archive/remediation/ai_usage_uncommitted_edit_2026-11-15.patch`; excluded
from release archives). The reconciliation above
credits him with the algorithm design and marks the formal specification as collaborative,
because the formal text was drafted by Opus. **Confirmed by Ali on 2026-11-15 (D-022).**

## Git authorship policy (D-025, decided by Ali: Option B)

| Option | What it means | Assessment |
|---|---|---|
| A | agent/bot Git identities as commit authors; Ali as committer or merger | most explicit in metadata; needs identities configured per agent |
| **B (adopted)** | Ali's identity as author, plus truthful trailers (`Co-Authored-By: <model>`) on every agent-produced commit, plus this ledger | keeps accountability with Ali, makes AI involvement visible in `git log`; rc2 already follows it |
| D-001 as is | Ali's identity, no model names; ledger only | git metadata alone does not show AI authorship (audit finding 9) |

Historical commits are not rewritten under any option.

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
| later (v1.0.0) | documentation, results, report | Opus |
| 3aa59a0 | docs: preserve lead's uncommitted attribution edit | Ali's edit, committed by Opus |
| c74ce82 … all later v1.0.1 commits | timing-phase, RSS, RQ1, literature, documentation remediation | Opus (see `REMEDIATION_LOG.md`) |

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
