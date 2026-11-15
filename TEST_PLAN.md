# Test Plan

**Status:** Validated: all layers pass for Python, C++17 and Rust (`make test`).

## 1. TDD workflow (mandatory)

| Stage | Rule | Evidence in Git |
|---|---|---|
| RED | expected behaviour and tests are written first and fail for the intended reason | `test:` commit precedes the matching `feat:` commit on each feature branch |
| GREEN | smallest implementation that passes; tests are never weakened | `feat:` commit; `tests/run_cases.py` passes |
| REFACTOR | structure/performance changes only, all tests re-run | separate `refactor:`/`perf:` commit |

Expected outputs are owned by the project lead. Implementation agents must not edit anything under
`fixtures/` or `tests/`; a disagreement is escalated, investigated against `ALGORITHM_SPEC.md`,
and, if the fixture is wrong, fixed in a separate `test:` commit with a decision-log entry.

## 2. Test layers

| Layer | Tool | Scope |
|---|---|---|
| Fixture consistency | `tests/check_fixtures.py` | hand-derived candidates == brute-force oracle |
| Conformance (integration + boundary + invalid input) | `tests/run_cases.py --impl X` | 39 cases, byte-identical outputs, error codes, exit codes |
| Unit (per language) | `python -m unittest`, `make -C cpp test`, `cargo test` | DNA validation, colour parsing, overlap validation, colour intersection, start/stop detection, frame tracking, candidate construction, cycle and repeat bounds |
| Cross-language | `tests/cross_language.py` | all three implementations byte-identical on every generated workload |
| Regression | new case under `fixtures/cases/R*` | every reproducible defect becomes a permanent case |
| Timing contract | `tests/test_timing_contract.py` | six phases, non-negative, total = sum, all implementations |
| RQ1 model | `tests/test_rq1_model.py` | true-sample support cases, ceilings, determinism, pairing, noise |
| RSS method | `tests/test_rss_measurement.py` | peak RSS independent of the harness |
| Release | `tests/check_release_archive.py ARCHIVE` | no private/VCS/build/OS/secret content; required files present |
| Static | `cargo fmt --check`, `cargo clippy -D warnings`, `-Wall -Wextra -Wpedantic -Werror` | code quality |

## 3. Required unit tests (each language)

DNA validation · identifier validation · colour parsing (`.`, ascending, rejects `2,1`, `1,x`,
`01`) · graph construction · overlap validation (bounds, mismatch, inconsistency) · colour-set
intersection · start-frame creation rule (`ATG`/`AT`/`A` at node end) · stop-codon detection
(all three) · reading-frame tracking across nodes with overlap · candidate record construction ·
cycle termination by visit bound · bounded repeat revisit · state-limit abort.

## 4. Coverage map: charter scenarios → cases

| Charter scenario | Cases |
|---|---|
| Single-node ORF | G01 |
| Multi-node ORF / overlap | G02 |
| Boundary-spanning codons | G03 (start), G08/G11 (stop spanning nodes) |
| Premature in-frame stop | G04 |
| Branching | G05, G06 |
| Cycles | G07, G11 |
| Repeats | G08, B08 |
| Strict / permissive support | G09, B10, B12, B13 |
| Invalid input | G10, E01–E15 |
| Empty graph, no start, no stop | B01, B02, B03 |
| Maximum lengths, state exhaustion | B04, B05, B06, B07, B09 |
| Multiple graphs | B11 |
