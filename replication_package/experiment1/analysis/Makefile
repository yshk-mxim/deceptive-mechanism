# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
PY := .venv/bin/python
RUFF := .venv/bin/ruff
.DEFAULT_GOAL := help

.PHONY: help check deps lint format types test mutation mutation-full analysis analysis-345 clean

help:  ## show targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | expand -t20

check: clean deps lint format types test mutation  ## offline gate for the shipped package

lint:
	$(RUFF) check src tests

format:
	$(RUFF) format --check src tests

types:
	.venv/bin/mypy

test:
	$(PY) -m pytest

deps:  ## dependency gate: CVEs and the runtime surface a replicator actually installs
	$(PY) ../../../harness/tools/dep_gate.py --profile analysis

mutation:  ## fast deterministic gate -- a surviving mutant is a vacuous test
	$(PY) ../../../harness/tools/mutation_sanity.py --suite analysis

mutation-full:  ## exhaustive cosmic-ray sweep (slow)
	.venv/bin/cosmic-ray init cosmic-ray.toml session.sqlite
	.venv/bin/cosmic-ray exec cosmic-ray.toml session.sqlite
	.venv/bin/cr-report session.sqlite

analysis:  ## reproduce every number in the paper from the shipped JSONL
	$(PY) -m deceit_analysis.cli

analysis-345:  ## reproduce every Experiment 3/4/5 number from the shipped JSONL
	$(PY) -m deceit_analysis.cli_345

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
