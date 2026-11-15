PYTHON ?= python3

.PHONY: check-fixtures build-cpp build-rust build unit-python unit-cpp unit-rust unit \
	lint-rust conformance cross test clean

check-fixtures:
	$(PYTHON) tests/check_fixtures.py

build-cpp:
	make -C cpp

build-rust:
	cd rust && cargo build --release

build: build-cpp build-rust

unit-python:
	$(PYTHON) -m unittest discover -s python/tests -v

unit-cpp:
	make -C cpp test

unit-rust:
	cd rust && cargo test

unit: unit-python unit-cpp unit-rust

lint-rust:
	cd rust && cargo fmt --check
	cd rust && cargo clippy --release --all-targets -- -D warnings

conformance: build
	$(PYTHON) tests/test_timing_contract.py
	$(PYTHON) tests/test_rq1_model.py
	$(PYTHON) tests/test_rss_measurement.py
	$(PYTHON) tests/test_cli_required_flags.py
	$(PYTHON) tests/check_readme_figures.py
	$(PYTHON) tests/run_cases.py --impl all

cross: build
	$(PYTHON) benchmarks/generate_workloads.py
	$(PYTHON) tests/cross_language.py

test: check-fixtures unit lint-rust conformance cross

clean:
	rm -rf cpp/build rust/target
	find python tests -name __pycache__ -type d -prune -exec rm -rf {} +
