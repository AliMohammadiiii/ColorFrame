# Input / Output Schema

**Status:** Frozen (schema version `1.1`, 2026-11-15: six timing phases). Shared by all three implementations.

All files are UTF-8 (ASCII content), tab-separated, `\n` line endings, with exactly one header
row. Fields never contain tabs. A trailing newline at end of file is optional on input and always
written on output. Blank lines are not allowed on input.

## 1. Inputs

### `nodes.tsv`

| Column | Type | Rule |
|---|---|---|
| `graph_id` | identifier | `[A-Za-z0-9_.-]+` |
| `node_id` | identifier | `[A-Za-z0-9_.-]+`, unique within `graph_id` |
| `sequence` | DNA | non-empty, characters `A`,`C`,`G`,`T` only (upper case) |
| `colors` | colour set | `.` for the empty set, otherwise strictly ascending, comma-separated non-negative integers without leading zeros (e.g. `1,2,7`) |

### `edges.tsv`

| Column | Type | Rule |
|---|---|---|
| `graph_id` | identifier | must also appear in `nodes.tsv` |
| `source` | node id | must exist in the same graph |
| `target` | node id | must exist in the same graph |
| `overlap_nt` | integer ≥ 0 | see `ALGORITHM_SPEC.md` §2.1 |

An edges file containing only the header is valid (graphs without edges).

### Numeric fields

- Colour values: decimal digits only, no sign, no leading zeros (`0` itself is allowed), value
  ≤ 2 147 483 647. Anything else → `INVALID_COLORS`.
- `overlap_nt`: must match `-?[0-9]+` and fit in a signed 64-bit integer, otherwise
  `MALFORMED_INPUT`. Negative values then fail with `INVALID_OVERLAP`.

## 2. Validation errors

Validation runs over the complete input before any search. On the first error the program writes
one line to standard error and exits with status **2**; no output files are written.

```
ERROR <CODE>: <human-readable message naming file, line and offending value>
```

Validation order (the first failing check wins):

1. `nodes.tsv` header, then each node row in file order: field count → `INVALID_ID` →
   `INVALID_DNA` → `INVALID_COLORS` → `DUPLICATE_NODE`.
2. `edges.tsv` header, then each edge row in file order: field count → `INVALID_ID` →
   integer `overlap_nt` (`MALFORMED_INPUT`) → `MISSING_NODE` → `DUPLICATE_EDGE` →
   `INVALID_OVERLAP` → `OVERLAP_MISMATCH`.
3. Per graph (ascending `graph_id`): `INCONSISTENT_OVERLAP`.

Each invalid fixture contains exactly one defect, and tests compare only `<CODE>`.

| Code | Condition |
|---|---|
| `MALFORMED_INPUT` | missing/wrong header, wrong number of fields, blank line, non-integer `overlap_nt` |
| `INVALID_ID` | `graph_id`/`node_id`/`source`/`target` violates the identifier pattern |
| `INVALID_DNA` | empty sequence or a character outside `ACGT` |
| `INVALID_COLORS` | colour field not `.` and not a strictly ascending list of non-negative integers |
| `DUPLICATE_NODE` | repeated `(graph_id, node_id)` |
| `MISSING_NODE` | edge references a node (or graph) absent from `nodes.tsv` |
| `DUPLICATE_EDGE` | repeated `(graph_id, source, target)` |
| `INVALID_OVERLAP` | `overlap_nt < 0`, `> len(source)`, or `≥ len(target)` |
| `OVERLAP_MISMATCH` | source suffix ≠ target prefix for the declared overlap |
| `INCONSISTENT_OVERLAP` | edges of one graph declare different overlaps |

Usage errors exit with status **64** and an `ERROR USAGE: <message>` line on standard error:
missing required flag, unknown flag, flag without value, non-integer limit value, limit below
its minimum (`ALGORITHM_SPEC.md` §3), invalid `--policy`, unreadable input or unwritable output
path. (Python implementations must override `argparse`'s default exit status 2.)
Successful runs exit with status **0**.

## 3. Command-line interface (identical for all implementations)

```
<impl> --nodes FILE --edges FILE --policy {strict|permissive|both}
       --out CANDIDATES.tsv --summary SUMMARY.tsv
       [--timings TIMINGS.tsv]
       [--max-orf-nt N] [--max-path-nodes N] [--max-node-visits N] [--max-states N]
```

| Implementation | Executable |
|---|---|
| Python | `python3 python/colorframe.py` (standard library only) |
| C++17 | `cpp/build/colorframe` |
| Rust | `rust/target/release/colorframe` |

## 4. Outputs

### `candidates.tsv`

```
graph_id  policy  candidate_id  path  start_offset  length_nt  sequence  support_colors  status
```

- `policy`: `strict` | `permissive`
- `path`: node ids joined by `>`
- `status`: `shared_support` | `fragmented_support`
- order and `candidate_id`: `ALGORITHM_SPEC.md` §4.5

### `summary.tsv`

```
graph_id  policy  search_states  max_depth  candidates  start_rejected  color_pruned  dead_ends
orf_length_cuts  path_length_cuts  node_visit_cuts  state_limit_hit  exhaustive
```

One row per `(graph_id, policy)` searched, sorted by `(graph_id, policy)`. Definitions:
`ALGORITHM_SPEC.md` §4.6. A graph that appears in `nodes.tsv` always gets a row, even with zero
candidates.

### `timings.tsv` (optional, not part of equivalence checks) — schema v1.1

```
phase  ms
```

Rows, in this order, with these exact boundaries:

| Row | Covers | Excludes |
|---|---|---|
| `parse` | reading both files, splitting rows/fields | validation |
| `validate` | every check of section 2, building graphs (sorted ids, sorted successors) | |
| `search` | traversal, candidate discovery and construction, colour-policy evaluation, the emit-time dedup set (spec 4.4) | any sorting, formatting, I/O |
| `canonicalize` | canonical ordering of runs and candidates (spec 4.5) | formatting, I/O |
| `write` | serialisation to TSV text and writing `--out` and `--summary` | the timings file itself |
| `total` | `parse` through `write` | interpreter/process start-up |

Timestamps are contiguous, so `total` equals the sum of the five phases (up to printing
precision). Milliseconds with 3 decimals from a monotonic clock (`time.perf_counter_ns`,
`std::chrono::steady_clock`, `std::time::Instant`). Process start-up is measured outside the
program by the benchmark harness (`wall_ms`). Contract test: `tests/test_timing_contract.py`.

With `--policy both`, every implementation searches each graph **strict first, then
permissive** (execution order); the output order is fixed by `canonicalize`.

## 5. Equivalence

Two runs are equivalent iff their `candidates.tsv` and `summary.tsv` files are **byte-identical**.
Because every field is canonical (sorted colours, fixed column order, integers without
padding, fixed sort order), byte identity is the comparison used by `tests/run_cases.py`.
