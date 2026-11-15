# ColorFrame — Project Charter

**Title:** ColorFrame: Algorithmic Trade-offs and Cross-language Performance of Frame-aware
Candidate Path Search in Colored Sequence Graphs

**Status:** v1.0.1 release candidate · charter version 1.1 · 2026-11-15

## 1. People and roles

| Role | Who | Responsibility |
|---|---|---|
| Project owner, research lead, chief architect, technical lead | **Ali Mohammadi** | Research direction, research questions, experimental comparisons, scope, approval of every decision that affects scientific meaning, final responsibility for the software and its interpretation. |
| Development agent (coordinator) | Claude Opus 5.5, high effort | Works under Ali's direction: drafts specifications and fixtures for Ali's review, decomposes tasks, delegates to the agents below, reviews and integrates their work, runs benchmarks, maintains documentation. |
| Development agent (implementation) | Claude Sonnet 5.5 | Python, C++17 and Rust implementations against the frozen specification and tests. |
| Development agent (supporting) | Claude Haiku 5.5 | Bounded tasks: literature metadata verification, CI configuration, supporting scripts. |

AI agents are tools directed by the project lead. Their contributions are recorded in
`AI_USAGE.md` and measured in `results/agent_usage.csv`. Nothing in this repository is presented
as hand-written by Ali unless it was.

## 2. Origin of the research idea

ColorFrame grew out of a technical discussion (November 2026) about annotating genomes in
single-cell metagenomic data: up to about one million bacterial cells per experiment, each
yielding a sparse, incomplete genome, typically summarised as a coloured de Bruijn graph (D-024). Questions raised there define this study:

- How should coding regions be found by walking a branching graph when one cannot follow every
  branch, and how should branches be chosen?
- What happens with cycles and repeats, and is a loop *in frame* or not?
- When can evidence from different cells (colours) safely be combined?
- How can this be made fast as well as correct?

Ali proposed turning these questions into a small, fully specified, testable experiment and
comparing the same algorithm in three languages, including the AI-assisted development effort.

## 3. Research questions

- **RQ1 — Evidence-support policies.** How do strict and permissive sample-support policies
  affect candidate recovery and extra candidate generation in branching sequence graphs?
- **RQ2 — Implementations.** How do Python, C++17 and Rust compare when implementing the same
  bounded, frame-aware graph traversal?
- **RQ3 — Computational trade-offs.** How do runtime, memory, throughput, branching and search
  limits interact?
- **RQ4 — AI-assisted development process (descriptive).** What AI assistance was used to produce
  each implementation? Reported as a descriptive process trace with incomplete telemetry; v1.0.1
  makes no inferential claim about effort versus performance (review finding F).

No answer is assumed in advance. This is an engineering and algorithmic study of a simplified
traversal problem, **not** a gene-calling system.

## 4. Scope

In scope (v1): simplified coloured sequence graph (nodes with DNA + colour sets, edges with a
uniform overlap), forward-strand `ATG`→stop ORF enumeration, two support policies, explicit
bounds with truncation reporting, three implementations, synthetic fixtures and generated
workloads, Modal benchmarks, R analysis, token accounting.

Out of scope (v1): real cDBG construction, reverse strand, alternative starts, gene scoring,
functional annotation, real-data ground truth. See `ALGORITHM_SPEC.md` §6 and `LIMITATIONS.md`.

## 5. Working principles

1. Specification and tests before implementation (TDD, `TEST_PLAN.md`).
2. Output equivalence across languages before any performance comparison.
3. Every bound that cuts the search is reported; a truncated search is never called exhaustive.
4. No fabricated results; missing telemetry is recorded as `NOT_EXPOSED`.
5. Every meaningful change is a Git commit with a Conventional Commit message.
6. Small, complete and reproducible beats large and unfinished.

## 6. Document map

| Document | Content |
|---|---|
| `ALGORITHM_SPEC.md` | authoritative algorithm (normative pseudocode, counters) |
| `INPUT_OUTPUT_SCHEMA.md` | file formats, CLI, error codes |
| `ARCHITECTURE.md` | components, repository layout, design decisions |
| `TEST_PLAN.md` | TDD workflow and test inventory |
| `fixtures/FIXTURES.md` | hand-derived ground truth |
| `BENCHMARK_PROTOCOL.md`, `MODAL_EXECUTION.md` | performance methodology |
| `TOKEN_ACCOUNTING.md`, `AI_USAGE.md` | AI-assisted development measurement |
| `LITERATURE_REVIEW.md`, `PRIOR_ART_AND_SCOPE.md`, `references.bib` | prior work |
| `LIMITATIONS.md`, `REPRODUCIBILITY.md`, `SECURITY.md` | caveats and operations |
| `TASK_BOARD.md`, `DECISION_LOG.md`, `CHANGELOG.md` | project management |
| `reports/TECHNICAL_REPORT.md` | final engineering and research report |
