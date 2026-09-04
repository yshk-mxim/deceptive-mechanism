# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Turn-resolved metric invariants.

The point of this arm is that Luo et al.'s headline Drift Rate is not the same quantity as
the two-point proxy reported elsewhere in this package. These tests pin that difference, so
the two cannot quietly converge through a coding error.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from deceit_analysis import turn_resolved

TRAJ = turn_resolved.TRAJECTORY


def rec(
    *,
    game: str,
    condition: str,
    probe: str,
    argmax: int,
    model: str = "m",
    readout_key: str = "R1",
    framing: str = "neutral",
    regime: str = "D",
    sampler_role: str = "none",
) -> dict[str, Any]:
    logprobs = [-9.0] * 10
    logprobs[argmax] = -0.1
    conditional = [math.exp(x) for x in logprobs]
    total = math.fsum(conditional)
    return {
        "model_key": model,
        "sampler_role": sampler_role,
        "readout_framing": framing,
        "readout_key": readout_key,
        "regime": regime,
        "game_id": f"{condition}-{game}",
        "condition": condition,
        "probe_point": probe,
        "candidate_logprobs": logprobs,
        "conditional": [c / total for c in conditional],
        "option_values": None,
    }


def trajectory(game: str, condition: str, targets: list[int]) -> list[dict[str, Any]]:
    return [
        rec(game=game, condition=condition, probe=p, argmax=t)
        for p, t in zip(TRAJ, targets, strict=True)
    ]


def test_a_trajectory_needs_every_probe_point() -> None:
    """A partial trajectory has a different denominator and is not their metric.

    Padding or truncating one would silently change `#changes / T`, so incomplete
    trajectories are dropped instead.
    """
    full = trajectory("0", "C0", [1, 2, 3, 4, 5, 6])
    assert len(turn_resolved.build_trajectories(full, "m")) == 1
    assert not turn_resolved.build_trajectories(full[:-1], "m")


def test_drift_rate_counts_changes_per_step_not_endpoints() -> None:
    """Their headline metric. A target that changes at every step scores 1.0."""
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 1, 2, 3, 4, 5])]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert report.drift_rate["C0"].estimate == pytest.approx(1.0)
    assert report.once_drift["C0"].estimate == pytest.approx(1.0)
    assert report.branch_drift["C0"].estimate == pytest.approx(1.0)


def test_branch_drift_can_miss_what_the_drift_rate_sees() -> None:
    """The reason two probe points are not enough, stated as a test.

    A target that changes and changes back is invisible at the endpoints: Branch D.R. reads
    0, while the Drift Rate correctly reports movement at two of five steps. Reporting the
    proxy as the headline metric would understate exactly the phenomenon under discussion.
    """
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [3, 3, 7, 7, 3, 3])]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert report.branch_drift["C0"].estimate == pytest.approx(0.0)
    assert report.once_drift["C0"].estimate == pytest.approx(1.0)
    assert report.drift_rate["C0"].estimate == pytest.approx(2 / 5)


def test_a_stable_target_gives_zero_on_every_drift_measure() -> None:
    """The positive control their design lacks: with a target present, drift must floor."""
    records = [r for i in range(4) for r in trajectory(str(i), "C1", [4] * 6)]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert report.drift_rate["C1"].estimate == pytest.approx(0.0)
    assert report.once_drift["C1"].estimate == pytest.approx(0.0)
    assert report.branch_drift["C1"].estimate == pytest.approx(0.0)


def test_step_profile_localises_when_the_target_moves() -> None:
    """*When* drift happens is the prediction two probe points cannot test.

    Under the paper's account the readout is prior reweighted by whatever constraints are in
    context, so drift should track information arriving rather than be flat across turns.
    """
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 1, 2, 2, 2, 2])]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert report.step_change["C0"] == pytest.approx([1.0, 1.0, 0.0, 0.0, 0.0])


def test_step_kl_is_measured_between_adjacent_probe_points() -> None:
    """Their KL is `D_KL(P_t || P_{t-1})`, not a distance to the first turn."""
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 0, 5, 5, 5, 5])]
    report = turn_resolved.analyse(records, "m", 400, 0)
    kl = report.step_kl["C0"]
    assert kl[0] == pytest.approx(0.0, abs=1e-9)
    assert kl[1] > 1.0
    assert kl[2] == pytest.approx(0.0, abs=1e-9)


def test_conditions_are_never_pooled() -> None:
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 1, 2, 3, 4, 5])] + [
        r for i in range(4) for r in trajectory(str(i), "C1", [4] * 6)
    ]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert report.drift_rate["C0"].estimate == pytest.approx(1.0)
    assert report.drift_rate["C1"].estimate == pytest.approx(0.0)


def test_override_and_bare_value_records_are_excluded() -> None:
    """Different instruments and different answer spaces are not extra paraphrases."""
    good = trajectory("0", "C0", [1, 2, 3, 4, 5, 6])
    override = [dict(r, readout_framing="sudo_override", readout_key="R0") for r in good]
    bare = [dict(r, option_values=["10"]) for r in good]
    assert len(turn_resolved.build_trajectories(good + override + bare, "m")) == 1


def test_an_absent_arm_reports_unrun() -> None:
    report = turn_resolved.analyse([], "m", 200, 0)
    assert report.trajectories == 0
    assert "UNRUN" in turn_resolved.render([report])


def test_render_shows_the_proxy_beside_the_headline_metric() -> None:
    """The difference between them is the reason this arm exists; it must be visible."""
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [3, 3, 7, 7, 3, 3])]
    rendered = turn_resolved.render([turn_resolved.analyse(records, "m", 400, 0)])
    assert "Drift Rate (#changes/T)" in rendered
    assert "Branch D.R." in rendered
    assert "Tier 1 rests on state identity" in rendered


def informative_trajectory(
    game: str, condition: str, targets: list[int], narrowing: list[bool]
) -> list[dict[str, Any]]:
    """A trajectory whose running consistent set shrinks only at the flagged steps."""
    sizes, size = [], 10
    for narrows in [False, *narrowing]:
        size -= 1 if narrows else 0
        sizes.append(size)
    return [
        rec(game=game, condition=condition, probe=p, argmax=t)
        | {"running_consistent_set": list(range(n))}
        for p, t, n in zip(TRAJ, targets, sizes, strict=True)
    ]


def test_drift_is_split_by_whether_the_step_carried_information() -> None:
    """The discriminating test between the two readings of drift.

    A filler question adds a turn and narrows nothing. Under "the belief drifts over time"
    a filler step should drift like any other; under "the readout tracks constraints
    arriving" it should not. The split has to be computable from the shipped records, or the
    claim is not reproducible.
    """
    records = [
        r
        for i in range(4)
        for r in informative_trajectory(
            str(i), "C0", [0, 1, 2, 2, 2, 2], [True, True, False, False, False]
        )
    ]
    report = turn_resolved.analyse(records, "m", 400, 0)
    informative, n_inf, filler, n_fil = report.drift_by_information["C0"]
    assert informative == pytest.approx(1.0)
    assert filler == pytest.approx(0.0)
    assert (n_inf, n_fil) == (8, 12)


def test_a_record_without_the_running_set_is_not_counted_as_filler() -> None:
    """An older file must degrade to "not measured", not to a silent False.

    Treating a missing field as "narrowed nothing" would count every step as filler and
    invert the result — the failure would look like a finding.
    """
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 1, 2, 3, 4, 5])]
    report = turn_resolved.analyse(records, "m", 400, 0)
    assert "C0" not in report.drift_by_information
    assert report.drift_rate["C0"].estimate == pytest.approx(1.0)


def test_the_information_split_is_rendered() -> None:
    records = [
        r
        for i in range(4)
        for r in informative_trajectory(
            str(i), "C0", [0, 1, 2, 2, 2, 2], [True, True, False, False, False]
        )
    ]
    rendered = turn_resolved.render([turn_resolved.analyse(records, "m", 400, 0)])
    assert "step narrowed nothing" in rendered


def c4_trajectory(
    game: str, targets: list[int], distractor: int, narrowing: list[bool], masses: list[float]
) -> list[dict[str, Any]]:
    """A C4 trajectory with an explicit distractor mass at each probe point."""
    sizes, size = [], 10
    for narrows in [False, *narrowing]:
        size -= 1 if narrows else 0
        sizes.append(size)
    out = []
    for p, t, n, m in zip(TRAJ, targets, sizes, masses, strict=True):
        record = rec(game=game, condition="C4", probe=p, argmax=t)
        conditional = [(1.0 - m) / 9] * 10
        conditional[distractor] = m
        record |= {
            "conditional": conditional,
            "distractor_index": distractor,
            "consistent_set": [0],
            # The distractor sits outside the running set once anything has narrowed, which
            # is how C4 is built.
            "running_consistent_set": [i for i in range(n) if n == 10 or i != distractor],
        }
        out.append(record)
    return out


def test_the_distractor_trajectory_is_reported_per_probe_point() -> None:
    """The two-point grid pools `early` and `late`, and for C4 those are different states.

    At `early` nothing has been asked, so the previous game's index is simply the most
    available candidate. Pooling reports the mean of the two and reads as though the model
    held the old target throughout — which is the claim under test.
    """
    masses = [0.56, 0.10, 0.10, 0.09, 0.09, 0.08]
    records = [
        r
        for i in range(4)
        for r in c4_trajectory(
            str(i), [7, 1, 1, 1, 1, 1], 7, [True, True, False, False, False], masses
        )
    ]
    report = turn_resolved.analyse(records, "m", 200, 0)
    assert report.distractor_mass == pytest.approx(masses, abs=1e-9)
    assert report.distractor_mass[0] > 5 * report.distractor_mass[-1]


def test_narrowing_steps_that_exclude_the_distractor_are_counted() -> None:
    """C4 places the distractor outside the consistent set, so constraints rule it out.

    Whether its mass then falls is what separates prior mass from a retained belief, and
    the count is what says the constraint actually bore on it.
    """
    masses = [0.56, 0.10, 0.10, 0.09, 0.09, 0.08]
    records = [
        r
        for i in range(4)
        for r in c4_trajectory(
            str(i), [7, 1, 1, 1, 1, 1], 7, [True, True, False, False, False], masses
        )
    ]
    report = turn_resolved.analyse(records, "m", 200, 0)
    excluded, narrowing = report.distractor_excluded
    assert narrowing == 8
    assert excluded == 8


def test_conditions_other_than_c4_do_not_produce_a_distractor_trace() -> None:
    """C0 has no distractor; reporting a trace for it would be reporting nothing."""
    records = [r for i in range(4) for r in trajectory(str(i), "C0", [0, 1, 2, 3, 4, 5])]
    report = turn_resolved.analyse(records, "m", 200, 0)
    assert report.distractor_mass == []
    assert "is the distractor retained" not in turn_resolved.render([report])


def test_a_missing_running_set_is_not_measured_rather_than_false() -> None:
    """The guard has to be tested at the unit, because the report cannot show it.

    If `_narrowed` returned False for a missing field, every step would be classed as
    filler, `informative` would stay empty, and the `informative and filler` guard would
    suppress the row anyway — so the report looks identical either way while the
    intermediate state is wrong. A later change that populated `informative` from another
    path would then silently report every step as uninformative, which inverts the finding.
    """
    with_field = {"running_consistent_set": [0, 1, 2]}
    fewer = {"running_consistent_set": [0, 1]}
    assert turn_resolved._narrowed(with_field, fewer) is True
    assert turn_resolved._narrowed(with_field, with_field) is False
    assert turn_resolved._narrowed({}, fewer) is None
    assert turn_resolved._narrowed(with_field, {}) is None
    assert turn_resolved._narrowed({"running_consistent_set": None}, fewer) is None
