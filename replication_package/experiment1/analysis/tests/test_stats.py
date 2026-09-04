# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Statistical machinery, checked against known values and against its own guarantees."""

from __future__ import annotations

import numpy as np
import pytest

from deceit_analysis import stats


def test_clopper_pearson_matches_published_values() -> None:
    """Textbook check: 0/10 and 10/10 have known exact bounds."""
    zero = stats.clopper_pearson(0, 10)
    assert zero.low == 0.0
    assert zero.high == pytest.approx(0.3085, abs=1e-3)
    full = stats.clopper_pearson(10, 10)
    assert full.high == 1.0
    assert full.low == pytest.approx(0.6915, abs=1e-3)


def test_clopper_pearson_interval_contains_the_estimate() -> None:
    for successes in range(21):
        interval = stats.clopper_pearson(successes, 20)
        assert interval.low <= interval.estimate <= interval.high


def test_clopper_pearson_rejects_impossible_input() -> None:
    with pytest.raises(ValueError):
        stats.clopper_pearson(5, 0)
    with pytest.raises(ValueError):
        stats.clopper_pearson(11, 10)


def test_binomial_gate_uses_the_interval_bound_not_the_point_estimate() -> None:
    """A small sample must not pass a gate on a lucky point estimate.

    6/6 is a proportion of 1.0 but its lower bound is only ~0.54, so a 0.90 gate must fail.
    This is the behaviour that keeps an underpowered cell from silently clearing a gate.
    """
    small = stats.binomial_gate(6, 6, 0.90, "min")
    assert small.proportion == 1.0
    assert not small.passed

    large = stats.binomial_gate(200, 200, 0.90, "min")
    assert large.passed


def test_binomial_gate_max_direction() -> None:
    """A `max` gate must use the upper bound."""
    assert stats.binomial_gate(0, 200, 0.15, "max").passed
    assert not stats.binomial_gate(60, 200, 0.15, "max").passed


def test_binomial_gate_rejects_an_unknown_direction() -> None:
    with pytest.raises(ValueError):
        stats.binomial_gate(1, 2, 0.5, "sideways")


def test_cluster_bootstrap_recovers_a_known_mean() -> None:
    clusters = [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]
    interval = stats.cluster_bootstrap(clusters, lambda a: float(np.mean(a)), 500, seed=1)
    assert interval.estimate == pytest.approx(2.0)
    assert interval.low <= 2.0 <= interval.high


def test_cluster_bootstrap_is_reproducible_from_the_seed() -> None:
    """Same seed must give the same interval; a different seed must actually resample.

    Uses enough clusters that distinct seeds reach distinct resample sets -- with only three
    clusters the percentile bounds coincide often enough to make the second assertion
    flaky, which is a property of the test, not of the estimator.
    """
    rng = np.random.default_rng(11)
    clusters = [list(rng.normal(loc, 0.3, 6)) for loc in rng.normal(0, 1.0, 20)]
    args = (clusters, lambda a: float(np.mean(a)), 400)
    assert stats.cluster_bootstrap(*args, seed=7) == stats.cluster_bootstrap(*args, seed=7)
    assert stats.cluster_bootstrap(*args, seed=7) != stats.cluster_bootstrap(*args, seed=8)


def test_cluster_bootstrap_is_wider_than_ignoring_clustering() -> None:
    """Resampling whole clusters must not understate uncertainty.

    Probes inside a game share a state; treating them as independent would shrink every
    interval and make Tier-2 look more precise than it is.
    """
    rng = np.random.default_rng(0)
    clusters = [list(rng.normal(loc, 0.05, 12)) for loc in rng.normal(0, 1.0, 8)]
    clustered = stats.cluster_bootstrap(clusters, lambda a: float(np.mean(a)), 800, seed=3)
    pooled = [[x] for cluster in clusters for x in cluster]
    naive = stats.cluster_bootstrap(pooled, lambda a: float(np.mean(a)), 800, seed=3)
    assert (clustered.high - clustered.low) > (naive.high - naive.low)


def test_cluster_bootstrap_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        stats.cluster_bootstrap([], lambda a: float(np.mean(a)), 10, seed=0)


def test_equivalence_concludes_for_a_tight_non_negative_distance() -> None:
    """A distance clearly below the margin, with real between-cluster spread."""
    rng = np.random.default_rng(5)
    clusters = [[abs(x)] for x in rng.normal(0.0, 0.005, 20)]
    _, equivalent = stats.equivalence_upper_bound(clusters, margin=0.10, resamples=800, seed=2)
    assert equivalent


def test_equivalence_rejects_a_real_effect() -> None:
    clusters = [[0.5, 0.5]] * 12
    _, equivalent = stats.equivalence_upper_bound(clusters, margin=0.10, resamples=500, seed=2)
    assert not equivalent


def test_equivalence_uses_the_interval_not_the_point_estimate() -> None:
    """The decisive case: a mean inside the margin whose upper bound is not.

    This is the test the old suite could not express. Both its TOST cases used zero-variance
    clusters, so `low == estimate == high` and substituting the point estimate for the
    interval bound was undetectable -- the exact substitution the function exists to prevent.
    Here the mean sits below 0.10 but the spread pushes the upper bound above it, so a
    point-estimate implementation would wrongly conclude equivalence.
    """
    rng = np.random.default_rng(11)
    values = np.abs(rng.normal(0.0, 0.12, 24))
    clusters = [[float(v)] for v in values]
    interval, equivalent = stats.equivalence_upper_bound(
        clusters, margin=0.10, resamples=1500, seed=3
    )
    assert interval.estimate < 0.10, "precondition: the point estimate is inside the margin"
    assert interval.high > 0.10, "precondition: the upper bound is outside it"
    assert not equivalent, "equivalence must be judged on the bound, not the estimate"


def test_equivalence_rejects_negative_observations() -> None:
    """A signed quantity needs a two-sided test; silently accepting it would mislabel."""
    with pytest.raises(ValueError, match="non-negative"):
        stats.equivalence_upper_bound([[0.1], [-0.1], [0.2]], margin=0.1, resamples=10, seed=0)


def test_equivalence_rejects_a_non_positive_margin() -> None:
    with pytest.raises(ValueError, match="margin must be positive"):
        stats.equivalence_upper_bound([[0.0], [0.0], [0.0]], margin=0.0, resamples=10, seed=0)


def test_cluster_bootstrap_refuses_degenerate_input() -> None:
    """Too few clusters gives a point interval, which equivalence reads as overwhelming support."""
    with pytest.raises(ValueError, match="at least"):
        stats.cluster_bootstrap([[0.05, 0.06]], lambda a: float(np.mean(a)), 100, seed=0)


def test_bootstrap_level_actually_changes_the_interval() -> None:
    """A 99% interval must be strictly wider than a 95% one, or `level` is being ignored."""
    rng = np.random.default_rng(7)
    clusters = [list(rng.normal(loc, 0.2, 5)) for loc in rng.normal(0, 1.0, 25)]
    narrow = stats.cluster_bootstrap(
        clusters, lambda a: float(np.mean(a)), 1200, seed=1, level=0.95
    )
    wide = stats.cluster_bootstrap(clusters, lambda a: float(np.mean(a)), 1200, seed=1, level=0.99)
    assert (wide.high - wide.low) > (narrow.high - narrow.low)


def test_holm_is_uniformly_more_powerful_than_bonferroni() -> None:
    """Holm must reject at least as much as Bonferroni, and strictly more here.

    With p = [0.01, 0.03] and alpha = 0.05, Bonferroni tests both against 0.025 and rejects
    only the first. Holm tests them step-down against 0.025 then 0.05 and rejects both.
    Hand-verified against the definition.
    """
    p_values = [0.01, 0.03]
    assert stats.holm_bonferroni(p_values, alpha=0.05) == [True, True]
    bonferroni = [p <= 0.05 / len(p_values) for p in p_values]
    assert bonferroni == [True, False]


def test_holm_break_is_not_replaceable_by_continue() -> None:
    """The step-down halt is required; skipping past a failure is anti-conservative.

    With p = [0.03, 0.031] and alpha = 0.05: rank 0 tests 0.03 against 0.025 and FAILS, so
    Holm rejects nothing. A `continue` would go on to test 0.031 against 0.05 and reject it.
    Both existing Holm tests happen to give identical output either way, so neither catches
    the substitution.
    """
    assert stats.holm_bonferroni([0.03, 0.031], alpha=0.05) == [False, False]


def test_holm_stops_at_the_first_failure_in_sorted_order() -> None:
    """The step-down halt is over *sorted* p-values, not input order.

    p = [0.001, 0.9, 0.002] is processed as 0.001, 0.002, 0.9: the first two clear
    0.0167 and 0.025, and 0.9 halts the procedure. So index 2 is rejected even though it
    appears after the large p-value in the input.
    """
    assert stats.holm_bonferroni([0.001, 0.9, 0.002], alpha=0.05) == [True, False, True]
    # And a genuine halt: 0.02 fails against alpha/3, so nothing beyond it is rejected.
    assert stats.holm_bonferroni([0.001, 0.02, 0.04, 0.6], alpha=0.05) == [
        True,
        False,
        False,
        False,
    ]


def test_holm_rejects_an_invalid_alpha() -> None:
    with pytest.raises(ValueError):
        stats.holm_bonferroni([0.01], alpha=0.0)


def test_hedges_g_is_zero_for_identical_samples_and_signed_otherwise() -> None:
    a = [1.0, 2.0, 3.0, 4.0]
    assert stats.hedges_g(a, a) == pytest.approx(0.0)
    assert stats.hedges_g([5.0, 6.0, 7.0], a) > 0.0
    assert stats.hedges_g(a, [5.0, 6.0, 7.0]) < 0.0


def test_hedges_g_matches_a_hand_computed_value() -> None:
    """Pin the value, not just the direction.

    a = [0, 1], b = [3, 4]: each variance is 0.5, pooled sd = sqrt(0.5), mean difference -3,
    so d = -4.242641. Correction factor 1 - 3/(4*4-9) = 1 - 3/7 = 0.571429, giving
    g = -2.424366. Asserting only that the correction shrinks the estimate leaves both the
    ddof and the correction constant free to be wrong; a ddof=0 implementation returns
    -3.428571 here and would pass a shrinkage-only assertion.
    """
    assert stats.hedges_g([0.0, 1.0], [3.0, 4.0]) == pytest.approx(-2.424366, abs=1e-6)


def test_hedges_g_uses_the_sample_variance() -> None:
    """ddof=0 would inflate every effect size; pin a case that distinguishes them."""
    value = stats.hedges_g([0.0, 1.0, 2.0], [5.0, 6.0, 7.0])
    assert value == pytest.approx(-4.0, abs=1e-9)


def test_hedges_g_handles_zero_variance() -> None:
    assert stats.hedges_g([2.0, 2.0], [2.0, 2.0]) == 0.0


def test_cliffs_delta_spans_minus_one_to_one() -> None:
    assert stats.cliffs_delta([3.0, 4.0], [1.0, 2.0]) == pytest.approx(1.0)
    assert stats.cliffs_delta([1.0, 2.0], [3.0, 4.0]) == pytest.approx(-1.0)
    assert stats.cliffs_delta([1.0, 2.0], [1.0, 2.0]) == pytest.approx(0.0)


def test_cliffs_delta_rejects_empty_samples() -> None:
    with pytest.raises(ValueError):
        stats.cliffs_delta([], [1.0])


def test_interval_excludes_is_inclusive_at_the_bounds() -> None:
    """Boundary behaviour, untested before: a value exactly on a bound is NOT excluded."""
    interval = stats.Interval(estimate=0.5, low=0.4, high=0.6)
    assert interval.excludes(0.3)
    assert interval.excludes(0.7)
    assert not interval.excludes(0.5)
    assert not interval.excludes(0.4), "a value on the lower bound is inside the interval"
    assert not interval.excludes(0.6), "a value on the upper bound is inside the interval"


def test_the_bf16_grid_is_recovered_from_a_scored_distribution() -> None:
    """The spacing scales with logit magnitude, so it cannot be a fixed constant."""
    for exponent, expected in ((3, 0.0625), (4, 0.125), (5, 0.25)):
        logits = [2.0**exponent + k * expected for k in (0, 1, 5, 17)]
        assert stats.grid_quantum(logits) == expected


def test_a_common_offset_does_not_change_the_grid() -> None:
    """Log-softmax subtracts `logsumexp` from every candidate, and it must cancel.

    This is the whole reason the grid survives into `candidate_logprobs`: the logprobs look
    like arbitrary reals, but their differences do not.
    """
    logits = [16.0, 16.125, 16.5, 17.0]
    shifted = [x - 3.14159 for x in logits]
    assert stats.grid_quantum(shifted) == stats.grid_quantum(logits) == 0.125


def test_an_ungridded_distribution_reports_no_quantum() -> None:
    assert stats.grid_quantum([0.0, 0.1, 0.2013, 0.30007]) is None


def test_a_single_value_has_no_grid() -> None:
    assert stats.grid_quantum([1.0]) is None


def test_the_resolution_floor_is_widest_at_one_half() -> None:
    """`dp = p(1-p)*quantum`, so the grid is coarsest in probability where `p` is least
    determined -- which is exactly where an equivalence margin has to do its work."""
    quantum = 0.0625
    assert stats.resolution_floor(0.5, quantum) > stats.resolution_floor(0.245, quantum)
    assert stats.resolution_floor(0.5, quantum) == pytest.approx(0.015625)
    # And it stays far under the SESOI the equivalence tests use.
    assert stats.resolution_floor(0.5, quantum) < 0.05


def test_a_one_sided_p_value_does_not_reward_the_wrong_direction() -> None:
    """The defect this replaces: a `GREATER` contrast whose effect ran *against* the
    prediction received the doubled two-sided tail, which is small for any large effect. In
    E5 an R1 of -0.187 scored 0.0005 and entered Holm as the family's most significant member.
    """
    wrong_way = np.full(2000, -0.2)
    assert stats.bootstrap_p_value(wrong_way, 2000, one_sided=True) == pytest.approx(1.0)
    # The same draws, judged two-sided, are maximally significant -- correctly, since a
    # two-sided test has no predicted direction to contradict.
    assert stats.bootstrap_p_value(wrong_way, 2000, one_sided=False) == pytest.approx(1 / 2000)


def test_a_one_sided_p_value_still_detects_the_predicted_direction() -> None:
    right_way = np.full(2000, 0.2)
    assert stats.bootstrap_p_value(right_way, 2000, one_sided=True) == pytest.approx(1 / 2000)


def test_the_p_value_floor_reflects_the_number_of_resamples() -> None:
    """A p of exactly zero would claim more resolution than the draws can supply."""
    for resamples in (100, 2000):
        draws = np.full(resamples, 0.2)
        assert stats.bootstrap_p_value(draws, resamples, one_sided=True) == pytest.approx(
            1 / resamples
        )


def test_a_split_bootstrap_gets_a_proportionate_one_sided_p() -> None:
    """Half the mass at or below zero is p = 0.5 one-sided, not a doubled 1.0."""
    draws = np.concatenate([np.full(1000, -0.1), np.full(1000, 0.1)])
    assert stats.bootstrap_p_value(draws, 2000, one_sided=True) == pytest.approx(0.5)
    assert stats.bootstrap_p_value(draws, 2000, one_sided=False) == pytest.approx(1.0)
