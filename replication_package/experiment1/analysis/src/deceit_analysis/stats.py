# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Statistics for the pre-registered tests (plan §7).

Cluster bootstrap resamples **games**, not probes: probes within a game share a scenario and
a state, so treating them as independent would understate every interval. Equivalence tests
are TOST, because the Tier-2 claims are null-shaped and a non-significant difference test
would be the wrong instrument for them.

Nothing here is imported by the harness, and this module imports nothing from it.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats as sps

#: A variance estimate needs at least two observations per sample.
MIN_SAMPLE_SIZE_FOR_VARIANCE = 2

#: Below this, a cluster bootstrap returns a degenerate (often zero-width) interval, which an
#: equivalence test would silently read as overwhelming support for the null.
MIN_CLUSTERS_FOR_BOOTSTRAP = 3


@dataclass(frozen=True, slots=True)
class Interval:
    """A point estimate with a confidence interval."""

    estimate: float
    low: float
    high: float
    level: float = 0.95

    def excludes(self, value: float) -> bool:
        """True if ``value`` lies outside the interval."""
        return value < self.low or value > self.high


@dataclass(frozen=True, slots=True)
class BinomialResult:
    """An exact binomial proportion with its interval and threshold verdict."""

    successes: int
    trials: int
    interval: Interval
    threshold: float
    direction: str
    passed: bool

    @property
    def proportion(self) -> float:
        """Observed proportion, or nan for zero trials."""
        return self.successes / self.trials if self.trials else math.nan


def clopper_pearson(successes: int, trials: int, level: float = 0.95) -> Interval:
    """Exact (Clopper-Pearson) binomial confidence interval.

    Exact rather than normal-approximation because several Tier-1 gates sit near 1.0, where
    a Wald interval can run above one and understate uncertainty.

    Raises:
        ValueError: if ``trials`` is not positive or ``successes`` is out of range.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= successes <= trials:
        raise ValueError("successes must lie in [0, trials]")
    alpha = 1.0 - level
    low = (
        0.0 if successes == 0 else float(sps.beta.ppf(alpha / 2, successes, trials - successes + 1))
    )
    high = (
        1.0
        if successes == trials
        else float(sps.beta.ppf(1 - alpha / 2, successes + 1, trials - successes))
    )
    return Interval(estimate=successes / trials, low=low, high=high, level=level)


def binomial_gate(
    successes: int, trials: int, threshold: float, direction: str, level: float = 0.95
) -> BinomialResult:
    """Test a proportion against a pre-registered threshold.

    The verdict uses the interval bound, not the point estimate: for a lower-bound gate the
    interval's *low* end must clear the threshold, so a small sample cannot pass on a lucky
    point estimate.

    Args:
        successes: Number of successes.
        trials: Number of trials.
        threshold: Pre-registered threshold.
        direction: ``"min"`` (proportion must be at least threshold) or ``"max"``.
        level: Confidence level.

    Returns:
        The result, including whether the gate passed.

    A gate with **zero trials is UNRUN, not passed**. `clopper_pearson` raises there, and
    rightly -- an interval on no data is meaningless -- but letting that exception escape
    would abort the whole analysis whenever one condition is absent, and the natural
    "fix" of skipping the gate is worse: a missing row reads as a test that passed. So a
    zero-trial gate returns the maximally uninformative interval [0, 1] with
    ``passed=False``, which no threshold in either direction can clear.

    Raises:
        ValueError: if ``direction`` is not "min" or "max".
    """
    if direction not in {"min", "max"}:
        raise ValueError("direction must be 'min' or 'max'")
    if trials == 0:
        return BinomialResult(
            successes=0,
            trials=0,
            interval=Interval(estimate=math.nan, low=0.0, high=1.0, level=level),
            threshold=threshold,
            direction=direction,
            passed=False,
        )
    interval = clopper_pearson(successes, trials, level)
    passed = interval.low >= threshold if direction == "min" else interval.high <= threshold
    return BinomialResult(
        successes=successes,
        trials=trials,
        interval=interval,
        threshold=threshold,
        direction=direction,
        passed=passed,
    )


def manipulation_check(
    successes: int, trials: int, threshold: float, level: float = 0.95
) -> BinomialResult:
    """Did the manipulation land in **these** states? Judged on the observed rate.

    **Deliberately not `binomial_gate`, and the difference is not pedantic.** A lower-bound
    gate at threshold `t` asks whether the *population* rate could be below `t`, and clearing
    it requires an observed rate well above `t`: at `n = 48` only `48/48` passes, at `n = 60`
    you need `59/60`, and at `n = 24` no result passes at all -- a perfect `24/24` fails.
    A pre-registration that says "accuracy at least 0.90" and implements a 0.90 lower bound has
    therefore written a gate demanding roughly 0.98.

    A manipulation check asks a different question. It is not estimating a population parameter
    from which these states were drawn; it is asking whether the states actually analysed
    represent what the context supplied. That is a property of the sample, so the observed rate
    is the statistic and the interval is context.

    The distinction matters most where the programme's claims are **existential**. Showing that
    a later report can fail to identify a prior commitment, or that a preferred truth can be
    realised as a falsehood, needs clear instances rather than a population estimate -- one
    black swan settles "all swans are white". An instrument tuned to reject population
    hypotheses will discard those instances for being too few.

    Confirmatory gates keep `binomial_gate`, where conservatism about a population rate is
    exactly right. This is for the checks.

    Args:
        successes: Correct answers.
        trials: States checked.
        threshold: Required observed accuracy.
        level: Confidence level for the reported interval.

    Returns:
        The result, with `passed` set from the **observed rate** and the interval reported
        alongside so a small sample is still visible.
    """
    if trials == 0:
        return BinomialResult(
            successes=0,
            trials=0,
            interval=Interval(estimate=0.0, low=0.0, high=1.0, level=level),
            threshold=threshold,
            direction="min",
            passed=False,
        )
    observed = successes / trials
    return BinomialResult(
        successes=successes,
        trials=trials,
        interval=clopper_pearson(successes, trials, level),
        threshold=threshold,
        direction="min",
        passed=observed >= threshold,
    )


#: How close to its threshold a check may sit before it is called marginal.
MARGINAL_BAND = 0.05


def marginal(result: BinomialResult, band: float = MARGINAL_BAND) -> bool:
    """Whether a passing check cleared its threshold only narrowly.

    Judging a manipulation check on the observed rate is right -- the question is about these
    states -- but it turns a continuum into a binary, and a check at exactly 0.90 against a
    0.90 threshold is not the same evidence as one at 1.000. A tenth of the states not
    representing the manipulation is a real caveat on any contrast computed over them.

    So the verdict stays binary and the closeness is reported alongside it, rather than
    letting `passed` carry the whole story in either direction.
    """
    return (
        result.passed
        and result.trials > 0
        and (result.successes / result.trials) - result.threshold < band
    )


def cluster_bootstrap(
    clusters: Sequence[Sequence[float]],
    statistic: Callable[[np.ndarray], float],
    resamples: int,
    seed: int,
    level: float = 0.95,
) -> Interval:
    """Bootstrap a statistic by resampling whole clusters with replacement.

    Args:
        clusters: One sequence of observations per cluster (game).
        statistic: Applied to the pooled observations of a resample.
        resamples: Number of bootstrap resamples.
        seed: RNG seed, recorded so the interval is reproducible.
        level: Confidence level.

    Returns:
        The point estimate and percentile interval.

    Raises:
        ValueError: if there are no clusters or no observations.
    """
    groups = [np.asarray(c, dtype=float) for c in clusters if len(c)]
    if len(groups) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        raise ValueError(
            f"cluster bootstrap needs at least {MIN_CLUSTERS_FOR_BOOTSTRAP} clusters, got "
            f"{len(groups)}: with fewer, every resample is the same data and the interval "
            "collapses to a point, which an equivalence test would read as the strongest "
            "possible evidence"
        )
    pooled = np.concatenate(groups)
    observed = float(statistic(pooled))

    rng = np.random.default_rng(seed)
    n = len(groups)
    draws = np.empty(resamples, dtype=float)
    for i in range(resamples):
        picks = rng.integers(0, n, size=n)
        draws[i] = statistic(np.concatenate([groups[j] for j in picks]))
    alpha = 1.0 - level
    low, high = np.quantile(draws, [alpha / 2, 1 - alpha / 2])
    return Interval(estimate=observed, low=float(low), high=float(high), level=level)


def equivalence_upper_bound(
    clusters: Sequence[Sequence[float]],
    margin: float,
    resamples: int,
    seed: int,
    level: float = 0.95,
) -> tuple[Interval, bool]:
    """One-sided upper confidence bound on the mean of a NON-NEGATIVE distance.

    Named for what it is. The previous implementation checked that a two-sided interval lay
    inside ``(-margin, +margin)`` -- but the statistics here are total variation and KL
    divergence, both non-negative, so the lower arm ``low > -margin`` is vacuously true for
    any data. The test was therefore one-sided already, evaluated at the 2.5% tail and
    labelled as a 95% TOST. That mislabelling was conservative rather than permissive, so it
    could not manufacture a false equivalence, but it advertised the wrong instrument.

    The correct instrument for "is this distance negligible" is a one-sided upper bound at
    ``level``: conclude equivalence iff the upper bound falls below the margin.

    Args:
        clusters: One sequence of observations per cluster (game).
        margin: Pre-registered negligibility margin, on the statistic's own scale.
        resamples: Bootstrap resamples.
        seed: RNG seed.
        level: One-sided confidence level.

    Returns:
        The interval (whose ``high`` is the one-sided bound) and whether equivalence holds.

    Raises:
        ValueError: if ``margin`` is not positive or any observation is negative.
    """
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if any(x < 0.0 for cluster in clusters for x in cluster):
        raise ValueError(
            "equivalence_upper_bound is for non-negative distances; a negative observation "
            "means the caller wants a two-sided test"
        )
    # A one-sided bound at `level` is the upper end of a two-sided interval at 2*level - 1.
    two_sided = max(0.0, 2.0 * level - 1.0)
    interval = cluster_bootstrap(clusters, lambda a: float(np.mean(a)), resamples, seed, two_sided)
    return interval, bool(interval.high < margin)


def holm_bonferroni(p_values: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down correction.

    Returns:
        Rejection decisions aligned to the input order.

    Raises:
        ValueError: if ``alpha`` is not in (0, 1).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    decisions = [False] * m
    for rank, idx in enumerate(order):
        if p_values[idx] <= alpha / (m - rank):
            decisions[idx] = True
        else:
            # Holm halts at the first failure by definition. It is NOT that larger p-values
            # would each fail their own threshold -- the thresholds increase with rank, so a
            # larger p-value can clear its own. Replacing this `break` with `continue` yields
            # a procedure that is anti-conservative and no longer Holm.
            break
    return decisions


def hedges_g(a: Sequence[float], b: Sequence[float]) -> float:
    """Hedges' *g*: standardised mean difference with the small-sample correction.

    Raises:
        ValueError: if either sample has fewer than two observations.
    """
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.size < MIN_SAMPLE_SIZE_FOR_VARIANCE or y.size < MIN_SAMPLE_SIZE_FOR_VARIANCE:
        raise ValueError("both samples need at least two observations")
    pooled_var = ((x.size - 1) * x.var(ddof=1) + (y.size - 1) * y.var(ddof=1)) / (
        x.size + y.size - 2
    )
    if pooled_var == 0.0:
        return 0.0
    d = (x.mean() - y.mean()) / math.sqrt(pooled_var)
    correction = 1.0 - 3.0 / (4.0 * (x.size + y.size) - 9.0)
    return float(d * correction)


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta: a non-parametric effect size in ``[-1, 1]``.

    Raises:
        ValueError: if either sample is empty.
    """
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.size == 0 or y.size == 0:
        raise ValueError("both samples must be non-empty")
    greater = int((x[:, None] > y[None, :]).sum())
    less = int((x[:, None] < y[None, :]).sum())
    return (greater - less) / (x.size * y.size)


#: Mantissa bits in bfloat16, the dtype the backends compute logits in. A bf16 value in
#: `[2**e, 2**(e+1))` sits on a grid of `2**(e - BF16_MANTISSA_BITS)`, so the spacing of
#: achievable logits scales with their magnitude and is **not** a fixed constant.
BF16_MANTISSA_BITS = 7

#: Coarsest dyadic grid worth searching for. Beyond this the search would start matching
#: numeric noise rather than a real quantisation grid.
_MAX_GRID_EXPONENT = 14

#: A grid needs at least two values to have a spacing at all.
_MIN_FOR_GRID = 2


def grid_quantum(values: Sequence[float], tolerance: float = 1e-6) -> float | None:
    """The finest dyadic grid every pairwise difference in `values` lands on.

    Logits are computed in bfloat16, so a scored distribution does not take arbitrary real
    values: within one state the achievable logits sit on a grid of `2**(e - 7)`, where `e` is
    the exponent of their magnitude. Log-softmax subtracts a common `logsumexp`, which cancels
    in any *difference*, so the grid survives into `candidate_logprobs` differences even though
    the logprobs themselves look continuous.

    This is why bit-identical `q_D` values recur across unrelated prompts. It is a property of
    the arithmetic, not evidence of a cache: two states that happen to land on the same grid
    point produce the same ratio to the last bit while their full logit vectors differ.

    Returns:
        The grid spacing, or `None` if no dyadic grid down to `2**-_MAX_GRID_EXPONENT` fits.
    """
    if len(values) < _MIN_FOR_GRID:
        return None
    base = values[0]
    deltas = [v - base for v in values[1:]]
    for exponent in range(_MAX_GRID_EXPONENT + 1):
        quantum = 2.0**-exponent
        if all(abs(d / quantum - round(d / quantum)) < tolerance for d in deltas):
            return quantum
    return None


def resolution_floor(p: float, quantum: float) -> float:
    """Smallest change in a two-candidate probability the logit grid can express.

    `p = sigmoid(gap)`, so `dp = p*(1-p) * d(gap)`, and the gap moves in steps of `quantum`.
    A contrast **smaller than this floor** on a single observation is below what the arithmetic
    can represent; over many states it is recoverable, because each state's grid is offset
    differently and the offsets dither the mean.
    """
    return p * (1.0 - p) * quantum


def bootstrap_p_value(
    draws: Sequence[float] | npt.NDArray[np.float64], resamples: int, *, one_sided: bool
) -> float:
    """Bootstrap p-value for a difference, matching the direction the contrast was declared in.

    **One-sided contrasts must not be scored on the doubled two-sided tail.** The doubled tail
    is `2 * min(P(draw <= 0), P(draw >= 0))`, which is small whenever the effect is *far* from
    zero — in either direction. Feeding that to a pre-registered `GREATER` test hands its
    smallest possible p-value to an effect running the wrong way: an `R1` of `-0.187`, a strong
    result contradicting the hypothesis, scored `0.0005` and entered Holm as the family's most
    significant member.

    For a one-sided contrast the p-value is the mass **at or below zero**, so a negative effect
    scores near 1 as it should.

    The floor of `1 / resamples` applies either way: a p of exactly zero would claim more
    resolution than the draws can supply.

    Takes an array as readily as a sequence. The callers in `utility` and `recipient` build their
    draws in a preallocated `np.empty(resamples)`, and the first thing done here is `np.asarray`,
    so the two are the same computation; the annotation said `Sequence[float]` only because it was
    written before those callers existed.
    """
    array = np.asarray(draws, dtype=float)
    if one_sided:
        return max(float((array <= 0.0).mean()), 1.0 / resamples)
    tail = float(min((array <= 0.0).mean(), (array >= 0.0).mean()))
    return max(2.0 * tail, 1.0 / resamples)
