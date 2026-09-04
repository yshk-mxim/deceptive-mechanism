# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""The record schema is the only thing binding the two stacks together.

The harness and the analysis package share no code — that separation is deliberate, so an
unportable inference dependency can never leak into the shipped artifact. What they do share
is the shape of a record. This contract test runs in *both* suites against the same schema
file, so a change cannot pass one stack while silently breaking the other.

It also pins the reserved fields. They are unused in Experiment 1 and exist so that
Experiments 2-4 need no migration: adding a nullable field now is free, adding one after
data collection is not.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "probe_record.v1.json"
RECORDS_PATH = Path(__file__).resolve().parents[2] / "data" / "records" / "tier1_records.jsonl"

#: Reserved for Experiments 2-4 (plan §9.1). Present, nullable, never populated here.
RESERVED_FIELDS = frozenset(
    {
        "injected_history_id",
        "injected_branch_label",
        "action_candidates",
        "recipient_state",
        "utility_condition",
        "persona_id",
        "provenance_condition",
        "selector_source",
        "judge_labels",
    }
)

#: Fields whose absence would make a Tier-1 claim unverifiable.
LOAD_BEARING_FIELDS = frozenset(
    {
        "tier",
        "state_digest",
        "logit_digest",
        "candidate_mass",
        "conditional",
        "sampler_role",
        "sampler_seed",
        "p_diverge",
        "realized_counts",
        "retrospective",
        "explanations",
        "pipeline_fingerprint",
    }
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def test_schema_exists_and_is_versioned(schema: dict) -> None:
    assert schema["$id"] == "probe_record.v1"
    assert schema["additionalProperties"] is False, "an open schema is not a contract"


def test_reserved_fields_are_present_and_nullable(schema: dict) -> None:
    """Experiments 2-4 must not need a schema migration."""
    properties = schema["properties"]
    for name in RESERVED_FIELDS:
        assert name in properties, f"reserved field {name} missing from the schema"
        assert name not in schema["required"], f"reserved field {name} must not be required"


def test_load_bearing_fields_are_present(schema: dict) -> None:
    missing = LOAD_BEARING_FIELDS - set(schema["properties"])
    assert not missing, f"schema is missing load-bearing fields: {sorted(missing)}"


def test_sampler_role_is_recorded_so_branch_instantiation_cannot_be_confused(
    schema: dict,
) -> None:
    """A raised temperature must be distinguishable from the deployment sampler.

    Plan §7.1: a `branch_instantiation` draw is valid for the retrospective measurement but
    may never support a claim about branching frequency under normal policy. That
    distinction has to live in the data, not in a convention someone remembers.
    """
    assert "sampler_role" in schema["properties"]
    assert "sampler_temperature" in schema["properties"]


@pytest.mark.skipif(not RECORDS_PATH.is_file(), reason="no shipped records yet")
def test_every_shipped_record_validates_against_the_schema() -> None:
    """Shipped data must match the shipped contract, field for field."""
    allowed = set(json.loads(SCHEMA_PATH.read_text())["properties"])
    required = set(json.loads(SCHEMA_PATH.read_text())["required"])
    with RECORDS_PATH.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            extra = set(record) - allowed
            missing = required - set(record)
            assert not extra, f"line {number}: undeclared fields {sorted(extra)}"
            assert not missing, f"line {number}: missing required fields {sorted(missing)}"


@pytest.mark.skipif(not RECORDS_PATH.is_file(), reason="no shipped records yet")
def test_reserved_fields_are_unpopulated_in_experiment_one() -> None:
    """If a reserved field ever carries a value here, the schema plan has drifted."""
    with RECORDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            for name in RESERVED_FIELDS:
                value = record.get(name)
                assert value in (None, {}, []), f"reserved field {name} populated: {value!r}"
