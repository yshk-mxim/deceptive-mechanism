# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Bare-value arm invariants.

The arm exists to check whether the index scheme creates the phenomenon, so the tests here
are about keeping the two arms comparable: the same field meanings, the same sensitivity
gate, and a positional statistic that measures list position rather than the answer itself.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from deceit_analysis import bare_value

THRESHOLDS = {"recovery_acc_min": 0.90}


#: A small stand-in for the real 00-99 space: twenty candidates, of which ten are offered.
#: Keeping the offered set a strict subset is what the arm is for -- with every candidate
#: offered, `option_share` is trivially 1 and half these tests would be vacuous.
SPACE = 20
OPTION_POSITIONS = list(range(5, 15))


def rec(
    *,
    game: str,
    condition: str,
    option_probs: list[float],
    model: str = "m",
    readout_key: str = "B1",
    probe_point: str = "late",
    candidate_mass: float = 0.9,
    outside: float = 0.0,
    consistent_set: list[int] | None = None,
    injected_index: int | None = None,
    entropy_bits: float = 1.0,
    sampler_role: str = "none",
) -> dict[str, Any]:
    """One bare-value probe over a 20-value space, ten of which were offered.

    ``option_probs`` is the distribution across the ten offered *positions in the list*;
    ``outside`` is the total conditional mass placed on values that were never shown.
    """
    conditional = [0.0] * SPACE
    for slot, position in enumerate(OPTION_POSITIONS):
        conditional[position] = option_probs[slot] * (1.0 - outside)
    for i in range(SPACE):
        if i not in OPTION_POSITIONS:
            conditional[i] = outside / (SPACE - len(OPTION_POSITIONS))
    return {
        "model_key": model,
        "sampler_role": sampler_role,
        "readout_key": readout_key,
        "game_id": f"{condition}-{game}",
        "condition": condition,
        "regime": "D",
        "probe_point": probe_point,
        "candidates": [f"{v:02d}" for v in range(SPACE)],
        "candidate_logprobs": [math.log(p) if p > 0 else -99.0 for p in conditional],
        "conditional": conditional,
        "option_values": [f"{v:02d}" for v in OPTION_POSITIONS],
        "consistent_set": consistent_set if consistent_set is not None else [OPTION_POSITIONS[0]],
        "candidate_mass": candidate_mass,
        "entropy_bits": entropy_bits,
        "injected_index": injected_index,
    }


def spike(i: int, n: int = 10) -> list[float]:
    out = [0.0] * n
    out[i] = 1.0
    return out


def uniform(n: int = 10) -> list[float]:
    return [1.0 / n] * n


# --------------------------------------------------------------------------- record keying


def test_only_bare_value_readouts_are_analysed() -> None:
    """An index-arm record reaching this module would be scored against the wrong space.

    Both arms write records with the same schema and the same field names, so nothing but
    the readout key separates them. Mixing them would silently average a 10-candidate
    distribution with a 100-candidate one.
    """
    records = [
        rec(game="0", condition="C0", option_probs=uniform(), readout_key="B1"),
        rec(game="0", condition="C0", option_probs=uniform(), readout_key="R1"),
    ]
    assert len(bare_value.bare_records(records, "m")) == 1


def test_sampled_records_are_excluded() -> None:
    """The readout claim is that nothing was decoded; a sampled record is not a readout."""
    records = [
        rec(game="0", condition="C0", option_probs=uniform()),
        rec(game="0", condition="C0", option_probs=spike(3), sampler_role="canonical"),
    ]
    assert len(bare_value.bare_records(records, "m")) == 1


def test_another_model_is_excluded() -> None:
    records = [
        rec(game="0", condition="C0", option_probs=uniform(), model="m"),
        rec(game="0", condition="C0", option_probs=uniform(), model="other"),
    ]
    assert len(bare_value.bare_records(records, "m")) == 1


# ------------------------------------------------------------------------ sensitivity gate


def test_recovery_counts_the_argmax_position_against_the_injected_index() -> None:
    """`injected_index` is a list position in both arms, so the gate is stated identically.

    Keeping the field meaning identical is what makes the two arms comparable at all: if
    this arm reported a value where the index arm reports a position, no number could be
    read across them.
    """
    # 40 trials, not 20: at n = 20 the exact lower bound for a perfect cell is 0.832, so
    # even flawless recovery fails a 0.90 min gate. The gate is right; the test would not be.
    records = [
        rec(game=str(i), condition="C1", option_probs=spike(4), injected_index=OPTION_POSITIONS[4])
        for i in range(40)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.recovery == (40, 40)
    assert report.recovery_passed


def test_a_failed_sensitivity_gate_is_flagged_as_uninterpretable_not_null() -> None:
    """An arm that cannot recover a present target says nothing about absence.

    This is the same rule as G2 in Tier 1, and the note matters more here: the bare-value
    arm's whole purpose is to check a null result, so a reader who takes its null at face
    value while the gate is failing has the argument exactly backwards.
    """
    records = [
        rec(game=str(i), condition="C1", option_probs=spike(1), injected_index=OPTION_POSITIONS[4])
        for i in range(20)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert not report.recovery_passed
    assert any("uninterpretable rather than null" in n for n in report.notes)


def test_a_c1_record_without_an_injected_index_is_not_a_recovery() -> None:
    records = [
        rec(game="0", condition="C1", option_probs=spike(0), injected_index=None),
        rec(game="1", condition="C1", option_probs=spike(0), injected_index=OPTION_POSITIONS[0]),
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.recovery == (1, 2)


# ------------------------------------------------------------------------------ option mass


def test_numeric_mass_and_option_share_are_separate_quantities() -> None:
    """Two facts the index arm cannot tell apart, because there every candidate is an option.

    `numeric_mass` is how often the model answers with a number at all; `option_share` is
    how much of that lands on a value it was actually shown. Collapsing them into one
    number would make a model that answers "seventeen" indistinguishable from one that
    answers 63 when 63 was never on the list.
    """
    records = [
        rec(game=str(i), condition="C0", option_probs=uniform(), candidate_mass=0.4, outside=0.25)
        for i in range(5)
    ] + [
        rec(game=str(i), condition="C1", option_probs=uniform(), candidate_mass=0.95, outside=0.0)
        for i in range(5)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=400, seed=0)
    assert report.numeric_mass["C0 late"].estimate == pytest.approx(0.4)
    assert report.numeric_mass["C1 late"].estimate == pytest.approx(0.95)
    assert report.option_share["C0 late"].estimate == pytest.approx(0.75)
    assert report.option_share["C1 late"].estimate == pytest.approx(1.0)


def test_option_positions_are_looked_up_by_name_not_assumed() -> None:
    """The offered values are a subset of the space, and not a contiguous or leading one.

    Assuming position i of `candidates` is option i would silently profile the wrong ten
    values -- and it would still produce a plausible-looking distribution.
    """
    record = rec(game="0", condition="C0", option_probs=uniform())
    assert bare_value.option_positions(record) == OPTION_POSITIONS


def test_numeric_mass_is_never_used_to_exclude_a_probe() -> None:
    """Filtering on it would condition the analysis on the dependent variable.

    A low value means the model would rather answer with a number it was not offered, which
    is information about the model. Every probe must still appear in every other statistic.
    """
    records = [
        rec(game=str(i), condition="C0", option_probs=spike(0), candidate_mass=0.001)
        for i in range(5)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.states == 5
    assert report.consistent_mass["C0 late"].estimate == pytest.approx(1.0)


# ------------------------------------------------------------------------ position profile


def test_the_position_profile_measures_list_position_not_the_value() -> None:
    """This is the F6 comparison, and it is only meaningful over positions.

    The candidate strings here are 10..19, so a profile keyed on the value would be shifted
    by ten and would not line up with the index arm's 0-9 at all.
    """
    records = [rec(game=str(i), condition="C0", option_probs=spike(2)) for i in range(5)]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert len(report.position_profile) == 10
    assert report.position_profile[2] == pytest.approx(1.0)
    assert report.position_profile[0] == pytest.approx(0.0)


def test_edge_and_interior_masses_reproduce_the_f6_statistic() -> None:
    """Edge is the mean of the first and last positions; interior is everything between."""
    profile = [0.02, 0.16, 0.16, 0.16, 0.10, 0.10, 0.10, 0.10, 0.08, 0.02]
    records = [rec(game=str(i), condition="C0", option_probs=profile) for i in range(5)]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.edge_mass == pytest.approx(0.02)
    assert report.interior_mass == pytest.approx(sum(profile[1:-1]) / 8)


def test_the_position_profile_uses_c0_only() -> None:
    """C1 has a target injected, so pooling it would wash out the prior being measured."""
    records = [rec(game=str(i), condition="C0", option_probs=spike(2)) for i in range(5)] + [
        rec(game=str(i), condition="C1", option_probs=spike(7), injected_index=OPTION_POSITIONS[7])
        for i in range(5)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.position_profile[2] == pytest.approx(1.0)
    assert report.position_profile[7] == pytest.approx(0.0)


# ----------------------------------------------------------------------------- absent arm


def test_an_absent_arm_reports_unrun_rather_than_empty_success() -> None:
    report = bare_value.analyse([], "m", THRESHOLDS, resamples=200, seed=0)
    assert report.states == 0
    assert any("UNRUN" in n for n in report.notes)
    assert "UNRUN" in bare_value.render([report])


def test_render_marks_the_arm_as_tier_2() -> None:
    """A Tier-2 result must never be readable as bearing on Tier 1."""
    records = [rec(game=str(i), condition="C0", option_probs=uniform()) for i in range(5)]
    rendered = bare_value.render(
        [bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)]
    )
    assert "Tier 2" in rendered
    assert "cannot disturb Tier 1" in rendered


def test_the_tables_are_split_by_probe_point() -> None:
    """Pooling `early` and `late` averages the contrast the whole argument rests on.

    At `early` no question has been asked and the readout is at chance; at `late` the
    constraints are in context. A pooled C0 number is the mean of the two and describes
    neither -- which is exactly the number this arm exists to compare against the index arm.
    """
    records = [
        rec(game=str(i), condition="C0", option_probs=spike(0), probe_point="late")
        for i in range(5)
    ] + [
        rec(game=str(i), condition="C0", option_probs=uniform(), probe_point="early")
        for i in range(5)
    ]
    report = bare_value.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert set(report.consistent_mass) == {"C0 early", "C0 late"}
    assert report.consistent_mass["C0 late"].estimate == pytest.approx(1.0)
    assert report.consistent_mass["C0 early"].estimate == pytest.approx(0.1)
