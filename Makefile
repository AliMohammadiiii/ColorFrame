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
	$(PYTHON) tests/run_cases.py --impl all

cross:
	@if [ -f tests/cross_language.py ]; then $(PYTHON) tests/cross_language.py; else echo "cross: tests/cross_language.py not present, skipping"; fi

test: check-fixtures unit lint-rust conformance cross

clean:
	rm -rf cpp/build rust/target
	find python tests -name __pycache__ -type d -prune -exec rm -rf {} +
