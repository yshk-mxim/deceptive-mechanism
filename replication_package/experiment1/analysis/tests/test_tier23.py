# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Tier-2 and Tier-3 aggregation invariants.

Every test here exists because a specific way of getting this wrong produced a number that
looked publishable. Two of them were caught only after the fact: a statistic that was
identically zero by construction, and an index whose key collisions made one condition stand
in for four. Both are asserted against now.
"""

from __future__ import annotations

from typing import Any

import pytest

from deceit_analysis import tier23

MARGIN_TV = 0.05
MARGIN_KL = 0.10
THRESHOLDS = {"tost_tv_margin": MARGIN_TV, "tost_kl_margin_bits": MARGIN_KL}


def rec(
    *,
    game: str,
    condition: str,
    conditional: list[float],
    model: str = "m",
    probe_point: str = "late",
    regime: str = "D",
    readout_key: str = "R1",
    framing: str = "neutral",
    consistent_set: list[int] | None = None,
    sampler_role: str = "none",
) -> dict[str, Any]:
    return {
        "model_key": model,
        "sampler_role": sampler_role,
        "game_id": f"{condition}-{game}",
        "condition": condition,
        "regime": regime,
        "probe_point": probe_point,
        "readout_key": readout_key,
        "readout_framing": framing,
        "conditional": conditional,
        "consistent_set": consistent_set if consistent_set is not None else [0],
    }


def uniform(n: int = 10) -> list[float]:
    return [1.0 / n] * n


def spike(index: int, n: int = 10) -> list[float]:
    out = [0.0] * n
    out[index] = 1.0
    return out


# ------------------------------------------------------------------------------- indexing


def test_index_admits_only_readout_records() -> None:
    """A branch-arm record shares its state key with the readout for the same state.

    Letting one overwrite the other made the Tier-2 result depend on file order, and half
    the time replaced a no-decoding measurement with a post-sampling one.
    """
    records = [
        rec(game="0", condition="C0", conditional=uniform()),
        rec(game="0", condition="C0", conditional=spike(3), sampler_role="canonical"),
    ]
    indexed = tier23._index(records, "m", "C0")
    assert len(indexed) == 1
    assert next(iter(indexed.values()))["conditional"] == uniform()


def test_index_raises_on_a_duplicate_state_key() -> None:
    """Last-write-wins is how the Tier-3 contrast was corrupted; it must be an error."""
    records = [
        rec(game="0", condition="C0", conditional=uniform()),
        rec(game="0", condition="C0", conditional=spike(3)),
    ]
    with pytest.raises(tier23.CorruptRecordSetError, match="duplicate record"):
        tier23._index(records, "m", "C0")


def test_a_duplicate_key_is_not_downgraded_to_a_note_by_analyse() -> None:
    """`analyse` turns an absent arm into a note; inconsistent data must still abort.

    If `CorruptRecordSetError` derived from ValueError, the broad except in `analyse` would
    swallow it and the run would report "unavailable" for a set that is actually corrupt.
    """
    assert not issubclass(tier23.CorruptRecordSetError, ValueError | KeyError)
    records = [
        rec(game="0", condition="C0", conditional=uniform()),
        rec(game="0", condition="C0", conditional=spike(3)),
    ]
    with pytest.raises(tier23.CorruptRecordSetError):
        tier23.analyse(records, "m", THRESHOLDS, resamples=50, seed=0)


def test_index_separates_regimes() -> None:
    """Regime D contributes 6 observations per game and U contributes 16 (see `analyse`)."""
    records = [
        rec(game="0", condition="C0", conditional=uniform(), regime="D"),
        rec(game="0", condition="C0", conditional=spike(1), regime="U"),
    ]
    assert len(tier23._index(records, "m", "C0", regime="D")) == 1
    assert len(tier23._index(records, "m", "C0", regime="U")) == 1
    with pytest.raises(tier23.CorruptRecordSetError):
        tier23._index(records, "m", "C0")


def test_index_separates_readout_framings() -> None:
    records = [
        rec(game="0", condition="C0", conditional=uniform(), framing="neutral"),
        rec(game="0", condition="C0", conditional=spike(1), framing="sudo_override"),
    ]
    assert len(tier23._index(records, "m", "C0", framing="sudo_override")) == 1
    assert (
        next(iter(tier23._index(records, "m", "C0", framing="neutral").values()))["conditional"]
        == uniform()
    )


def test_game_key_strips_the_condition_so_conditions_line_up() -> None:
    """C0 and C3 are content-matched on `(seed, regime, index)`, not on condition."""
    c0 = rec(game="7", condition="C0", conditional=uniform())
    c3 = rec(game="7", condition="C3", conditional=uniform())
    assert tier23._game_key(c0) == tier23._game_key(c3) == "7"


# ----------------------------------------------------------------------------- pairing


def test_unmatched_probes_are_skipped_not_paired_arbitrarily() -> None:
    left = {("0", "late", "R1"): {"x": 1.0}, ("1", "late", "R1"): {"x": 2.0}}
    right = {("0", "late", "R1"): {"x": 5.0}}
    grouped, dropped = _paired(left, right)
    assert set(grouped) == {"0"}
    assert dropped == 0


def test_non_finite_pairs_are_counted_rather_than_silently_dropped() -> None:
    """An infinite KL is where "the prior explains the readout" is *most* false.

    Discarding it in silence would condition the analysis on the dependent variable, which
    is the failure mode the pre-registration forbids elsewhere.
    """
    left = {("0", "late", "R1"): {"x": float("inf")}, ("1", "late", "R1"): {"x": 1.0}}
    right = {("0", "late", "R1"): {"x": 0.0}, ("1", "late", "R1"): {"x": 0.0}}
    grouped, dropped = _paired(left, right)
    assert dropped == 1
    assert set(grouped) == {"1"}


def _paired(left: Any, right: Any) -> Any:
    return tier23._paired_by_game(left, right, lambda a, b: a["x"] - b["x"])


def test_pairs_are_grouped_by_game_not_flattened() -> None:
    """Probes inside one game share a state; flattening them understates every interval."""
    left = {
        ("0", "late", "R1"): {"x": 1.0},
        ("0", "late", "R2"): {"x": 2.0},
        ("1", "late", "R1"): {"x": 3.0},
    }
    right = {k: {"x": 0.0} for k in left}
    grouped, _ = _paired(left, right)
    assert {g: sorted(v) for g, v in grouped.items()} == {"0": [1.0, 2.0], "1": [3.0]}


# --------------------------------------------------------------------- T9 framing effect


def test_t9_is_zero_when_c0_and_c3_readouts_agree() -> None:
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform()),
            rec(game=str(i), condition="C3", conditional=uniform()),
        )
    ]
    out = tier23.commitment_framing_effect(records, "m", MARGIN_TV, 400, 0, regime="D")
    assert out.n_games == 6
    assert out.interval.estimate == pytest.approx(0.0)
    assert out.equivalent


def test_t9_detects_a_framing_difference_larger_than_the_margin() -> None:
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=spike(0)),
            rec(game=str(i), condition="C3", conditional=spike(1)),
        )
    ]
    out = tier23.commitment_framing_effect(records, "m", MARGIN_TV, 400, 0, regime="D")
    assert out.interval.estimate == pytest.approx(1.0)
    assert not out.equivalent


# ------------------------------------------------------------------ T10 prior x constraints


def test_t10_is_not_identically_zero_in_regime_d() -> None:
    """The defect that made this test meaningless: renormalising both sides.

    In Regime D the consistent set has one element, and renormalising over it returns [1.0]
    for *any* distribution, so KL([1.0] || [1.0]) = 0 regardless of the data. The statistic
    must depend on where the readout actually puts its mass.
    """
    matched = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=spike(0), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
        )
    ]
    spread = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
        )
    ]
    close = tier23.prior_times_constraints(matched, "m", MARGIN_KL, 400, 0, regime="D")
    far = tier23.prior_times_constraints(spread, "m", MARGIN_KL, 400, 0, regime="D")
    assert close.interval.estimate != pytest.approx(far.interval.estimate)
    assert far.interval.estimate > close.interval.estimate


def test_t10_defaults_to_the_structure_matched_prior() -> None:
    """C5 is a two-message prompt; comparing it to a thirteen-message C0 adds structure."""
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=spike(0)),
            rec(game=str(i), condition="C6", conditional=uniform()),
            rec(game=str(i), condition="C5", conditional=spike(9)),
        )
    ]
    out = tier23.prior_times_constraints(records, "m", MARGIN_KL, 400, 0, regime="D")
    assert out.name.endswith("C6")
    assert "C6" in out.description


def test_t10_skips_states_where_the_constraint_excludes_nothing() -> None:
    """A consistent set covering the whole support carries no constraint to explain."""
    full = list(range(10))
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), consistent_set=full),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=full),
        )
    ]
    out = tier23.prior_times_constraints(records, "m", MARGIN_KL, 400, 0, regime="D")
    assert out.n_games == 0
    assert out.dropped == 6


# ------------------------------------------------------------------- T3 override contrast


def test_override_contrast_is_keyed_per_condition() -> None:
    """The retracted finding: a key without the condition let C4 stand in for all four.

    Here C0's override readout is identical to its neutral one while C4's is maximally
    different. A condition-blind index reports one pooled number and hides both.
    """
    records: list[dict[str, Any]] = []
    for i in range(6):
        records += [
            rec(game=str(i), condition="C0", conditional=uniform(), framing="neutral"),
            rec(
                game=str(i),
                condition="C0",
                conditional=uniform(),
                framing="sudo_override",
                readout_key="R0",
            ),
            rec(game=str(i), condition="C4", conditional=spike(0), framing="neutral"),
            rec(
                game=str(i),
                condition="C4",
                conditional=spike(1),
                framing="sudo_override",
                readout_key="R0",
            ),
        ]
    out = tier23.override_framing_contrast(records, "m", 400, 0)
    assert set(out) == {"C0/R0", "C4/R0"}
    assert out["C0/R0"][0].estimate == pytest.approx(0.0)
    assert out["C4/R0"][0].estimate == pytest.approx(1.0)
    assert out["C0/R0"][1] == out["C4/R0"][1] == 6


def test_override_contrast_compares_only_matched_states() -> None:
    """An override at `late` must not be compared against a neutral readout at `early`."""
    records = [
        rec(game="0", condition="C0", conditional=spike(0), probe_point="early"),
        rec(
            game="0",
            condition="C0",
            conditional=spike(5),
            probe_point="late",
            framing="sudo_override",
            readout_key="R0",
        ),
    ]
    assert tier23.override_framing_contrast(records, "m", 100, 0) == {}


def test_override_contrast_averages_over_neutral_paraphrases() -> None:
    """Each override record is compared against every neutral paraphrase at that state."""
    records: list[dict[str, Any]] = []
    for i in range(6):
        records += [
            rec(game=str(i), condition="C0", conditional=spike(0), readout_key="R1"),
            rec(game=str(i), condition="C0", conditional=spike(1), readout_key="R2"),
            rec(
                game=str(i),
                condition="C0",
                conditional=spike(0),
                framing="sudo_override",
                readout_key="R0",
            ),
        ]
    out = tier23.override_framing_contrast(records, "m", 400, 0)
    # TV against R1 is 0, against R2 is 1: the mean is 0.5, not either endpoint.
    assert out["C0/R0"][0].estimate == pytest.approx(0.5)


# ------------------------------------------------------------------------------- analyse


def test_analyse_reports_regimes_separately() -> None:
    """Pooling weights a U game 2.7x a D game, so the pooled number describes neither."""
    records = [
        r
        for regime in ("D", "U")
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), regime=regime),
            rec(game=str(i), condition="C3", conditional=uniform(), regime=regime),
        )
    ]
    report = tier23.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    names = {o.name for o in report.equivalences}
    assert any(n.endswith("[D]") for n in names)
    assert any(n.endswith("[U]") for n in names)


def test_an_absent_arm_becomes_a_note_rather_than_a_silent_pass() -> None:
    records = [rec(game=str(i), condition="C0", conditional=uniform()) for i in range(6)]
    report = tier23.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert not report.equivalences
    assert any("UNRUN" in n or "unavailable" in n for n in report.notes)
    assert any("Luo replication UNRUN" in n for n in report.notes)


def test_render_marks_tier23_as_not_bearing_on_tier1() -> None:
    """The separation is the paper's central methodological claim; it must survive rendering."""
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform()),
            rec(game=str(i), condition="C3", conditional=uniform()),
        )
    ]
    rendered = tier23.render([tier23.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)])
    assert "do not bear on Tier 1" in rendered
    assert "T9_commitment_framing_adds_nothing[D]" in rendered
    assert "one-sided upper bound" in rendered


# ------------------------------------------------------------------ elicitation robustness


def test_paraphrase_agreement_is_one_when_every_paraphrase_agrees() -> None:
    records = [
        rec(game=str(i), condition="C0", conditional=uniform(), readout_key=k)
        for i in range(6)
        for k in ("R1", "R2", "R3")
    ]
    out = tier23.paraphrase_agreement(records, "m", 400, 0)
    assert out is not None
    tv, observed, chance = out
    assert tv.estimate == pytest.approx(1.0)
    # Identical paraphrases: cross-paraphrase draw agreement is exactly the chance baseline,
    # which is the point of reporting the baseline. Raw agreement of 0.1 on a uniform
    # ten-candidate readout would otherwise read as near-total instability.
    assert observed.estimate == pytest.approx(chance.estimate)
    assert chance.estimate == pytest.approx(0.1)


def test_paraphrase_agreement_falls_when_paraphrases_disagree() -> None:
    """Disagreement between wordings is elicitation sensitivity, not a commitment moving."""
    records = [
        rec(game=str(i), condition="C0", conditional=spike(j), readout_key=k)
        for i in range(6)
        for j, k in enumerate(("R1", "R2", "R3"))
    ]
    out = tier23.paraphrase_agreement(records, "m", 400, 0)
    assert out is not None
    tv, observed, chance = out
    assert tv.estimate == pytest.approx(0.0)
    # Each paraphrase is certain of a different candidate: two draws from one paraphrase
    # always agree, two draws across paraphrases never do. The gap is total.
    assert chance.estimate == pytest.approx(1.0)
    assert observed.estimate == pytest.approx(0.0)


def test_a_concentrated_readout_does_not_look_stable_by_itself() -> None:
    """The failure the chance baseline exists to prevent (Lanham et al. 2023, App. B).

    Three paraphrases that each put 0.9 on a *different* candidate disagree almost totally,
    yet a chance-blind reading of their draw agreement against a uniform prior would call
    them far more consistent than a uniform readout that agrees perfectly.
    """

    def near(i: int) -> list[float]:
        out = [0.1 / 9] * 10
        out[i] = 0.9
        return out

    records = [
        rec(game=str(g), condition="C0", conditional=near(j), readout_key=k)
        for g in range(6)
        for j, k in enumerate(("R1", "R2", "R3"))
    ]
    out = tier23.paraphrase_agreement(records, "m", 400, 0)
    assert out is not None
    _tv, observed, chance = out
    assert chance.estimate > observed.estimate
    assert chance.estimate - observed.estimate > 0.5


def test_paraphrase_agreement_excludes_the_override_probe() -> None:
    """R0 carries a system clause the neutral paraphrases do not.

    Pooling it would report a framing effect as paraphrase noise, which is the same
    conflation that produced the retracted Tier-3 finding.
    """
    records = [
        rec(game=str(i), condition="C0", conditional=uniform(), readout_key=k)
        for i in range(6)
        for k in ("R1", "R2")
    ] + [
        rec(
            game=str(i),
            condition="C0",
            conditional=spike(0),
            readout_key="R0",
            framing="sudo_override",
        )
        for i in range(6)
    ]
    out = tier23.paraphrase_agreement(records, "m", 400, 0)
    assert out is not None
    assert out[0].estimate == pytest.approx(1.0)


def test_turn_drift_pairs_early_with_late_at_the_same_paraphrase() -> None:
    """Pairing across paraphrases would measure wording sensitivity as drift."""
    records = [
        rec(game=str(i), condition="C0", conditional=spike(0), probe_point="early", readout_key=k)
        for i in range(6)
        for k in ("R1", "R2")
    ] + [
        rec(game=str(i), condition="C0", conditional=spike(1), probe_point="late", readout_key=k)
        for i in range(6)
        for k in ("R1", "R2")
    ]
    out = tier23.turn_drift(records, "m", 400, 0)
    assert out is not None
    assert out.estimate == pytest.approx(1.0)


def test_turn_drift_is_zero_when_the_readout_does_not_move() -> None:
    records = [
        rec(game=str(i), condition="C0", conditional=uniform(), probe_point=p)
        for i in range(6)
        for p in ("early", "late")
    ]
    out = tier23.turn_drift(records, "m", 400, 0)
    assert out is not None
    assert out.estimate == pytest.approx(0.0)


# --------------------------------------------------------------------- Luo truncation


def descending(n: int = 10) -> list[float]:
    """A distribution with ten *distinct* probabilities, so a rank cut is well defined.

    A uniform distribution cannot express partial truncation at all: every candidate ties at
    the cut, so either all survive or none do. Building the fixture on distinct values keeps
    "exactly `kept` candidates survive" a meaningful instruction.
    """
    weights = [2.0**-i for i in range(n)]
    total = sum(weights)
    return [w / total for w in weights]


def trunc_rec(*, game: str, probe: str, conditional: list[float], kept: int) -> dict[str, Any]:
    """A C0 record whose top-64 window puts exactly ``kept`` candidates inside the top 20."""
    import math

    logprobs = [math.log(p) if p > 0 else -40.0 for p in conditional]
    ordered = sorted(logprobs, reverse=True)
    # A window whose 20th value sits just below the `kept`-th candidate, so exactly `kept`
    # candidates clear the cut.
    cut = ordered[kept - 1] - 1e-9
    top = [ordered[0] + 1.0] * (tier23.LUO_TOP_K - 1) + [cut] + [cut - 1.0] * 44
    return {
        "model_key": "m",
        "sampler_role": "none",
        "game_id": f"C0-{game}",
        "condition": "C0",
        "regime": "D",
        "probe_point": probe,
        "readout_key": "R1",
        "readout_framing": "neutral",
        "conditional": conditional,
        "candidate_logprobs": logprobs,
        "topk_logprobs": top,
        "consistent_set": [0],
    }


def test_truncation_counts_states_where_a_candidate_falls_outside_the_window() -> None:
    """Their -9999 makes a dropped candidate impossible, not merely unlikely."""
    records = [
        trunc_rec(game=str(i), probe=p, conditional=descending(), kept=kept)
        for i in range(6)
        for p, kept in (("early", 10), ("late", 4))
    ]
    out = tier23.truncation_effect(records, "m", 200, 0)
    assert out["states"] == 6
    assert out["states_with_a_truncated_candidate"] == 6


def test_no_truncation_is_reported_when_every_candidate_is_inside_the_window() -> None:
    records = [
        trunc_rec(game=str(i), probe=p, conditional=descending(), kept=10)
        for i in range(6)
        for p in ("early", "late")
    ]
    out = tier23.truncation_effect(records, "m", 200, 0)
    assert out["states_with_a_truncated_candidate"] == 0
    assert out["mean_kl_full_support"] == pytest.approx(out["mean_kl_luo_truncated"])


def test_truncation_can_make_the_kl_literally_infinite() -> None:
    """The measurable claim: the same states, the same KL, two answers.

    Both probes carry the same distribution, so the full-support KL is exactly zero and any
    difference can only come from the truncation. Assigning -9999 to a dropped candidate
    does not make it unlikely, it makes it impossible, and a KL against a zero is unbounded.
    Reported turn-to-turn "instability" of that shape is measuring the sentinel.
    """
    # Both probes carry the SAME distribution, so the full-support KL is exactly zero and
    # any difference can only come from the truncation. The early probe -- the reference
    # side of the KL -- loses eight candidates to the window, and their probability does not
    # shrink, it becomes zero.
    same = descending()
    records = [
        trunc_rec(game=str(i), probe="early", conditional=same, kept=2) for i in range(6)
    ] + [trunc_rec(game=str(i), probe="late", conditional=same, kept=10) for i in range(6)]
    out = tier23.truncation_effect(records, "m", 400, 0)
    assert out["states_with_a_truncated_candidate"] == 6
    assert out["states_with_infinite_truncated_kl"] == 6
    assert "mean_kl_full_support" not in out, (
        "every truncated KL here is infinite, so there is nothing finite to average"
    )


def test_a_short_topk_window_is_not_read_as_truncation() -> None:
    """Claiming a candidate fell outside a window shorter than the cut is an inference
    from missing data, not an observation."""
    records = [
        trunc_rec(game=str(i), probe=p, conditional=descending(), kept=2)
        for i in range(6)
        for p in ("early", "late")
    ]
    for record in records:
        record["topk_logprobs"] = record["topk_logprobs"][:5]
    out = tier23.truncation_effect(records, "m", 200, 0)
    assert out["states_with_a_truncated_candidate"] == 0


def test_a_partially_truncated_state_still_yields_a_finite_inflated_kl() -> None:
    """Not every truncation is fatal, and the finite cases are where the size shows.

    When the truncated candidates carry no probability in the *other* turn, the KL stays
    finite but grows: mass is redistributed onto the survivors. Without a case like this the
    module would only ever report infinities and the mean columns would be dead code.
    """
    p = descending()
    q = list(reversed(descending()))
    records = [trunc_rec(game=str(i), probe="late", conditional=p, kept=10) for i in range(6)] + [
        trunc_rec(game=str(i), probe="early", conditional=q, kept=10) for i in range(6)
    ]
    baseline = tier23.truncation_effect(records, "m", 400, 0)
    assert baseline["states_with_infinite_truncated_kl"] == 0
    assert baseline["mean_kl_full_support"] == pytest.approx(baseline["mean_kl_luo_truncated"])

    tighter = [trunc_rec(game=str(i), probe="late", conditional=p, kept=6) for i in range(6)] + [
        trunc_rec(game=str(i), probe="early", conditional=q, kept=10) for i in range(6)
    ]
    out = tier23.truncation_effect(tighter, "m", 400, 0)
    assert out["states_with_a_truncated_candidate"] == 6
    assert out["states_with_infinite_truncated_kl"] == 0
    assert out["mean_kl_luo_truncated"] != pytest.approx(out["mean_kl_full_support"])


def test_bare_value_records_are_excluded_from_the_index_index() -> None:
    """`option_values` marks the bare-value arm; it is not a paraphrase of C0."""
    bare = rec(game="0", condition="C0", conditional=uniform())
    bare["option_values"] = ["10", "11"]
    bare["readout_key"] = "B1"
    indexed = rec(game="0", condition="C0", conditional=uniform())
    assert len(tier23._index([indexed, bare], "m", "C0")) == 1


def test_index_refuses_to_mix_candidate_spaces() -> None:
    """Mixing supports would surface as `total_variation` raising, which `analyse` turns
    into a note -- so the union would degrade to "unavailable" rather than fail."""
    wide = rec(game="1", condition="C0", conditional=[1.0 / 20] * 20)
    records = [rec(game="0", condition="C0", conditional=uniform()), wide]
    with pytest.raises(tier23.CorruptRecordSetError, match="mixes candidate spaces"):
        tier23._index(records, "m", "C0")


def test_the_kl_magnitude_moves_with_the_floor_and_the_tv_does_not() -> None:
    """Why T10 is reported twice: the KL's size is a property of the floor constant.

    The pre-registered KL verdict is sound -- a readout with most of its mass outside the
    consistent set is nowhere near the margin for any floor small enough to mean "excluded"
    -- but its magnitude describes the floor, not the model. TV answers the same question
    with nothing to choose.
    """
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
        )
    ]
    original = tier23._KL_FLOOR
    seen = []
    try:
        for floor in (1e-3, 1e-9):
            tier23._KL_FLOOR = floor
            seen.append(
                tier23.prior_times_constraints(
                    records, "m", MARGIN_KL, 400, 0, regime="D"
                ).interval.estimate
            )
    finally:
        tier23._KL_FLOOR = original
    assert seen[1] > seen[0] * 2, "the KL magnitude should track the floor"

    tv = [
        tier23.prior_times_constraints_tv(records, "m", MARGIN_TV, 400, 0, regime="D")
        for _ in range(1)
    ]
    assert 0.0 <= tv[0].interval.estimate <= 1.0


def test_the_tv_companion_reaches_the_same_verdict() -> None:
    """Both must reject when the prior does not explain the readout, and accept when it does."""
    mismatched = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
        )
    ]
    matched = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=spike(0), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
        )
    ]
    assert not tier23.prior_times_constraints_tv(
        mismatched, "m", MARGIN_TV, 400, 0, regime="D"
    ).equivalent
    assert tier23.prior_times_constraints_tv(matched, "m", MARGIN_TV, 400, 0, regime="D").equivalent


def test_both_t10_variants_are_reported() -> None:
    """A reader given only the KL would quote a number that describes a constant."""
    records = [
        r
        for i in range(6)
        for r in (
            rec(game=str(i), condition="C0", conditional=uniform(), consistent_set=[0]),
            rec(game=str(i), condition="C6", conditional=uniform(), consistent_set=[0]),
            rec(game=str(i), condition="C3", conditional=uniform()),
        )
    ]
    report = tier23.analyse(records, "m", THRESHOLDS, resamples=400, seed=0)
    names = {o.name for o in report.equivalences}
    assert any(n.startswith("T10_prior_times_constraints") for n in names)
    assert any(n.startswith("T10_tv_prior_times_constraints") for n in names)
    assert "not interpretable" in tier23.render([report])


def test_two_override_probes_are_never_pooled() -> None:
    """R0 and R0S are different instruments, not two samples of one.

    R0 carries Luo et al.'s Number Guessing clause, R0S the stronger Entity Guessing one.
    Pooling them would report their average as a single measurement — the same error as
    pooling conditions, one level down, and it would hide exactly the comparison the pair
    exists to make.
    """
    records: list[dict[str, Any]] = []
    for i in range(6):
        records += [
            rec(game=str(i), condition="C0", conditional=uniform(), readout_key="R1"),
            rec(
                game=str(i),
                condition="C0",
                conditional=uniform(),
                framing="sudo_override",
                readout_key="R0",
            ),
            rec(
                game=str(i),
                condition="C0",
                conditional=spike(0),
                framing="sudo_override",
                readout_key="R0S",
            ),
        ]
    out = tier23.override_framing_contrast(records, "m", 400, 0)
    assert set(out) == {"C0/R0", "C0/R0S"}
    assert out["C0/R0"][0].estimate == pytest.approx(0.0)
    assert out["C0/R0S"][0].estimate == pytest.approx(0.9)


def test_truncation_is_reported_per_probe_framing() -> None:
    """Their KL is computed on their own probe, so the two instruments are not averaged.

    Pooling their override readout with our neutral paraphrases would report a mean across
    two different instruments as though it were one measurement — the same error as pooling
    conditions, and the row that bears on their reported numbers is the override one.
    """
    records: list[dict[str, Any]] = []
    for i in range(6):
        for probe, kept in (("early", 10), ("late", 4)):
            records.append(trunc_rec(game=str(i), probe=probe, conditional=descending(), kept=kept))
            over = trunc_rec(game=str(i), probe=probe, conditional=descending(), kept=10)
            over["readout_framing"] = "sudo_override"
            over["readout_key"] = "R0"
            records.append(over)
    report = tier23.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)
    assert report.truncation["neutral"]["states_with_a_truncated_candidate"] == 6
    assert report.truncation["R0"]["states_with_a_truncated_candidate"] == 0
    rendered = tier23.render([report])
    assert "| R0 |" in rendered, "each override probe gets its own row"
    assert "| neutral |" in rendered


def test_the_two_override_probes_are_never_pooled() -> None:
    """`R0` and `R0S` share a framing and are different instruments.

    `R0` is Luo's Listing 1 clause — the probe this experiment replicates — and `R0S` is
    Listing 3's stronger one. Filtering on framing alone averaged them, and the published F15
    magnitudes were that average: 3.684 bits reported against 3.511 for `R0` alone on Gemma,
    with the two truncated candidates coming entirely from `R0S`. `override_framing_contrast`
    already filtered on the readout key for this reason; `truncation_effect` did not.
    """
    records: list[dict[str, Any]] = []
    for i in range(6):
        for probe, kept_r0, kept_r0s in (("early", 10, 10), ("late", 10, 4)):
            for key, kept in (("R0", kept_r0), ("R0S", kept_r0s)):
                rec = trunc_rec(game=str(i), probe=probe, conditional=descending(), kept=kept)
                rec["readout_framing"] = "sudo_override"
                rec["readout_key"] = key
                records.append(rec)
    report = tier23.analyse(records, "m", THRESHOLDS, resamples=200, seed=0)

    assert "R0" in report.truncation and "R0S" in report.truncation
    assert "sudo_override" not in report.truncation, "the pooled row must be gone"
    # Only R0S truncates here; a pooled row would have reported half of it against R0's name.
    assert report.truncation["R0"]["states_with_a_truncated_candidate"] == 0
    assert report.truncation["R0S"]["states_with_a_truncated_candidate"] == 6
    assert report.truncation["R0"]["states"] == report.truncation["R0S"]["states"] == 6
