# Token Accounting

**Status:** v1.0.1 — a **descriptive AI-assisted development process trace**, not an inferential study (review finding F).

Why the totals are incomplete: several agent legs ended in API errors without exposed usage; the coordinating agent's (Opus) usage is never exposed, including all v1.0.1 remediation work (D-023); there is one implementation episode per language; human development time was not recorded. Recorded totals are therefore lower bounds, and the differences between languages are smaller than the unrecorded parts.

| Quantity | Value |
|---|---|
| Model tokens (completed subagent legs) | see ledger below |
| Opus (shared architecture, review, remediation) | NOT_EXPOSED |
| Human development time | not recorded |
| Modal compute, authoritative v1.0.1 run | 179.5 s container wall time (`pipeline.log`), plus a 34 s R analysis and two small probes |
| Modal cost | NOT_EXPOSED (dashboard only) |
| Model API cost | NOT_EXPOSED (no per-agent input/output split) |

## What the harness exposes

| Agent | Exposed per completed leg | Not exposed |
|---|---|---|
| Sonnet / Haiku subagents | total tokens, tool calls, duration | input/output split, cache read/write, reasoning tokens, cost; anything for legs that ended in an API error |
| Opus coordinator (this session) | the current context size only (≈314 k tokens of a 1 M window at the time of recording) | cumulative input/output tokens, cache, cost |

Missing values are recorded as `NOT_EXPOSED` in `results/agent_usage.csv` and never estimated.
`total_tokens` was added to the charter's column list because it is the only token figure the
harness reports for subagents.

## Ledger summary (completed legs only)

| Category | Agent | Recorded tokens | Tool calls | Duration (s) | API restarts | Conformance failures before pass |
|---|---|---:|---:|---:|---:|---|
| Python implementation | Sonnet | 108 958 | 8 | 117.4 | 1 | 1 run (fixture errors, not code) |
| C++17 implementation | Sonnet | 116 682 | 9 | 184.0 | 1 | 1 run (fixture errors, not code) |
| Rust implementation | Sonnet | 126 251 | 5 | 61.5 | 2 | 0 (ran after the fixture fix) |
| Shared: CI | Haiku | 75 172 | 11 | 52.0 | 0 | – |
| Docs: literature verification | Haiku | 90 884 | 5 | 43.8 | 1 | – |
| Shared: architecture, tests, tooling, review, docs | Opus | NOT_EXPOSED | NOT_EXPOSED | NOT_EXPOSED | – | – |

**Interpretation limits.** Every implementation lost at least one leg whose usage is not
recorded: the first leg of each was cut off by the spend limit, and Rust also lost a second leg
to a network error, during which it wrote most of its code. Recorded totals are therefore
**lower bounds**, and the gap differs by language. The Rust figure in particular reflects
mostly verification work. Shared Opus effort (specification, fixtures, review) is not allocated
to any language. No conclusion about "which language needs less AI effort" is supported by these
numbers.

## Costs

- **Model API cost:** `NOT_EXPOSED` per agent. Account-level: the plan's extra-usage budget was
  exhausted during this session (≈ USD 50.27 of a USD 50.00 monthly cap, read from the plan
  usage endpoint on 2026-11-14). That amount covers all use of the account, not only this
  project, so it is not attributed to ColorFrame.
- **Modal compute cost:** tracked separately. Container wall time is in
  `results/modal/<run>/pipeline.log`; the billed amount is in the Modal dashboard
  (`NOT_EXPOSED` here).

Pricing used for any estimate: none. No estimate is made without per-agent input/output token
counts.
