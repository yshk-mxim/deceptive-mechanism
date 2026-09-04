# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Tier-2 mechanism characterisation and the Tier-3 Luo replication.

**Neither can disturb Tier 1.** Tier 1 rests on state identity, which is a fact about how
the transcripts were built; these analyses ask what distribution the generated reports are
drawn from, and how much of Luo et al.'s reported instability belongs to their instrument.

The two Tier-2 equivalence tests are the interesting ones:

* **C0 vs C3** -- does commitment framing add anything beyond the in-context constraints?
* **C0 vs prior x constraints** -- does the model's marginal prior (C5), renormalised over
  the constraint-consistent set, account for the readout with no commitment term at all?

Both are TOST against margins fixed on substantive grounds before collection. A failure of
either is a live finding about what the model is doing, and leaves the Tier-1 result intact.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from deceit_analysis import metrics
from deceit_analysis.stats import (
    MIN_CLUSTERS_FOR_BOOTSTRAP,
    Interval,
    cluster_bootstrap,
    equivalence_upper_bound,
)

#: Probability floor for candidates outside the consistent set when reweighting a prior.
#: Without it, KL is infinite whenever the readout favours an excluded candidate -- which is
#: precisely the disconfirming case, so it must contribute a large finite value rather than
#: be dropped.
_KL_FLOOR = 1e-6


@dataclass(slots=True)
class EquivalenceOutcome:
    """One equivalence test with its margin and verdict."""

    name: str
    tier: int
    description: str
    interval: Interval
    margin: float
    equivalent: bool
    n_games: int
    #: Pairs excluded as undefined or infinite. Reported, never silently absorbed.
    dropped: int = 0


@dataclass(slots=True)
class Tier23Report:
    """Tier-2 and Tier-3 outcomes for one model."""

    model_key: str
    equivalences: list[EquivalenceOutcome] = field(default_factory=list)
    override_contrast: dict[str, tuple[Interval, int]] = field(default_factory=dict)
    #: Tier 3: the same early-to-late KL under full support and under Luo's truncation,
    #: keyed by readout framing. Their KL is computed on their own probe, so the override
    #: and neutral rows are separate measurements and are never averaged together.
    truncation: dict[str, dict[str, float | int]] = field(default_factory=dict)
    #: Tier 2: ``(mean 1 - TV, observed draw agreement, chance baseline)`` across the
    #: neutral paraphrases at one state.
    paraphrase: tuple[Interval, Interval, Interval] | None = None
    #: Tier 2: how far the readout moves between the early and late probe points.
    drift: Interval | None = None
    notes: list[str] = field(default_factory=list)


class CorruptRecordSetError(Exception):
    """Two records claim the same state key, so the set does not describe one experiment.

    Deliberately **not** a ``ValueError``: `analyse` converts ValueError into a note and
    carries on, which is right for an arm that is merely absent but wrong for data that is
    internally inconsistent. Silently discarding a colliding record is what produced the
    retracted Tier-3 finding, so this must abort rather than degrade.
    """


def _sorted_clusters(groups: dict[Any, list[float]]) -> list[list[float]]:
    """Clusters in a deterministic order.

    The point estimate does not depend on the order clusters are supplied in; the percentile
    bounds do. Insertion order follows the order records were read, so a reader who concatenates
    the input files differently gets different interval bounds. `utility._cluster` already sorts;
    this does the same for every other call site.
    """
    return [groups[k] for k in sorted(groups)]


def _game_key(record: dict[str, Any]) -> str:
    """Strip the condition prefix so matched games line up across conditions."""
    key: str = record["game_id"].split("-", 1)[1]
    return key


def _index(
    records: list[dict[str, Any]],
    model_key: str,
    condition: str,
    *,
    regime: str | None = None,
    framing: str | None = None,
    readout_key: str | None = None,
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Index readout records by (game, probe point, readout) for state-matched comparison.

    Only ``sampler_role == "none"`` records are indexed. A branch-arm record shares its key
    with the readout record for the same state, so indexing both would make the result depend
    on file order.

    A duplicate key raises rather than resolving last-write-wins. Silent overwriting here is
    not a lost record but a changed comparison: where four records share a key, three vanish
    and the survivor is compared against everything, which is a different statistic wearing
    the same name.

    Raises:
        CorruptRecordSetError: if two records claim the same key.
    """

    def selected(record: dict[str, Any]) -> bool:
        return (
            record["model_key"] == model_key
            and record["condition"] == condition
            and record["sampler_role"] == "none"
            # A bare-value record is a different answer space, not a different paraphrase.
            and record.get("option_values") is None
            and (regime is None or record["regime"] == regime)
            and (framing is None or record["readout_framing"] == framing)
            # **A framing is not an instrument.** `R0` and `R1`-`R3` differ in framing, but
            # `R0` and `R0S` share `sudo_override` and are two different probes: Luo's
            # Listing 1 clause and Listing 3's stronger one. Filtering on framing alone pools
            # them, which `override_framing_contrast` avoids by filtering on the key and
            # `truncation_effect` did not -- reporting their average as one measurement.
            and (readout_key is None or record["readout_key"] == readout_key)
        )

    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        if not selected(record):
            continue
        key = (_game_key(record), record["probe_point"], record["readout_key"])
        if key in out:
            raise CorruptRecordSetError(
                f"duplicate record for {model_key}/{condition} at {key}; refusing to "
                "silently discard one"
            )
        out[key] = record
    widths = {len(r["conditional"]) for r in out.values()}
    if len(widths) > 1:
        raise CorruptRecordSetError(
            f"{model_key}/{condition} mixes candidate spaces of sizes {sorted(widths)}; "
            "these records do not describe one experiment"
        )
    return out


def _paired_by_game(
    left: dict[tuple[str, str, str], dict[str, Any]],
    right: dict[tuple[str, str, str], dict[str, Any]],
    statistic: Any,
) -> tuple[dict[str, list[float]], int]:
    """Compute a paired statistic for every matched probe, grouped by game.

    Grouping by game is what the cluster bootstrap resamples: probes inside one game share a
    scenario and a state, so treating them as independent would understate every interval.

    Returns:
        ``(grouped values by game, count of pairs dropped as undefined or infinite)``.
    """
    grouped: dict[str, list[float]] = defaultdict(list)
    dropped = 0
    for key, a in left.items():
        b = right.get(key)
        if b is None:
            continue
        value = statistic(a, b)
        if value is None or not math.isfinite(value):
            # Never drop silently. An infinite KL is exactly the case where "the prior
            # explains the readout" is most false, so discarding it would condition the
            # analysis on the dependent variable -- the failure mode the pre-registration
            # forbids elsewhere.
            dropped += 1
            continue
        grouped[key[0]].append(value)
    return grouped, dropped


def _bounded_or_unrun(
    grouped: dict[str, list[float]],
    dropped: int,
    margin: float,
    resamples: int,
    seed: int,
    **outcome: Any,
) -> EquivalenceOutcome:
    """Build an equivalence outcome, or an explicitly UNRUN one if there is too little data.

    `cluster_bootstrap` refuses fewer than three clusters, and rightly. But letting that
    exception propagate loses the one number that explains why: how many pairs were
    dropped. An arm where every pair was undefined and an arm that was never collected are
    different facts, and the report must be able to tell them apart.

    An UNRUN outcome is never ``equivalent``: absence of a measurement is not evidence of
    negligible distance.
    """
    if len(grouped) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return EquivalenceOutcome(
            interval=Interval(estimate=math.nan, low=math.nan, high=math.nan, level=0.95),
            margin=margin,
            equivalent=False,
            n_games=len(grouped),
            dropped=dropped,
            **outcome,
        )
    interval, equivalent = equivalence_upper_bound(list(grouped.values()), margin, resamples, seed)
    return EquivalenceOutcome(
        interval=interval,
        margin=margin,
        equivalent=equivalent,
        n_games=len(grouped),
        dropped=dropped,
        **outcome,
    )


def commitment_framing_effect(
    records: list[dict[str, Any]],
    model_key: str,
    margin: float,
    resamples: int,
    seed: int,
    regime: str | None = None,
) -> EquivalenceOutcome:
    """TOST on TV(C0, C3): does commitment framing add anything beyond the constraints?"""
    grouped, dropped = _paired_by_game(
        _index(records, model_key, "C0", regime=regime),
        _index(records, model_key, "C3", regime=regime),
        lambda a, b: metrics.total_variation(a["conditional"], b["conditional"]),
    )
    interval, equivalent = equivalence_upper_bound(list(grouped.values()), margin, resamples, seed)
    return EquivalenceOutcome(
        name="T9_commitment_framing_adds_nothing",
        tier=2,
        description="TV between the C0 readout and the constraint-only C3 readout",
        interval=interval,
        margin=margin,
        equivalent=equivalent,
        n_games=len(grouped),
        dropped=dropped,
    )


def prior_times_constraints(
    records: list[dict[str, Any]],
    model_key: str,
    margin: float,
    resamples: int,
    seed: int,
    prior_condition: str = "C6",
    regime: str | None = None,
) -> EquivalenceOutcome:
    """TOST on KL(C0 readout ‖ prior reweighted onto the consistent set), over FULL support.

    Two properties of this comparison are load-bearing, and dropping either makes it
    meaningless on the pre-registered arm.

    **The support is the full ten indices, never the consistent set.** Renormalising both
    sides over the consistent set would make the statistic identically zero: in Regime D that
    set has exactly one element, and renormalising over one element returns ``[1.0]`` for
    *any* ``p``, so KL([1.0] ‖ [1.0]) is 0 with no dependence on the data. The test would then
    "confirm" the paper's own Tier-2 hypothesis with a zero-width interval. Over the full
    support it measures the quantity of interest: how much mass the readout puts *outside*
    the constraint-consistent set.

    **The prior must be structure-matched.** C5 is a two-message prompt while C0 at ``late``
    is thirteen, so their difference is partly conversational. C6 carries C0's framing and
    turn count with universally-true questions, so it isolates the constraint effect.

    Args:
        records: All records.
        model_key: Model to analyse.
        margin: Equivalence margin in bits, fixed before collection.
        resamples: Bootstrap resamples.
        seed: Bootstrap seed.
        prior_condition: Which prior condition to use as the reference.
        regime: Restrict to one regime, or None to require the caller to have done so.

    Returns:
        The equivalence outcome.
    """
    prior = _index(records, model_key, prior_condition, regime=regime)

    def statistic(a: dict[str, Any], b: dict[str, Any]) -> float | None:
        consistent = a["consistent_set"]
        if len(consistent) >= len(a["conditional"]):
            return None  # nothing is excluded, so there is no constraint to explain
        # Reweight the prior onto the consistent set but keep the FULL support, so mass the
        # readout places outside that set is what the divergence measures.
        floor = _KL_FLOOR
        mass = math.fsum(b["conditional"][i] for i in consistent)
        if mass <= 0.0:
            return None
        reweighted = [
            (b["conditional"][i] / mass if i in set(consistent) else floor)
            for i in range(len(b["conditional"]))
        ]
        total = math.fsum(reweighted)
        reweighted = [x / total for x in reweighted]
        return metrics.kl_divergence_bits(a["conditional"], reweighted)

    grouped, dropped = _paired_by_game(
        _index(records, model_key, "C0", regime=regime), prior, statistic
    )
    return _bounded_or_unrun(
        grouped,
        dropped,
        margin,
        resamples,
        seed,
        name=f"T10_prior_times_constraints_vs_{prior_condition}",
        tier=2,
        description=(
            f"KL(C0 readout ‖ {prior_condition} prior reweighted onto the consistent set), "
            "bits, over full support"
        ),
    )


def prior_times_constraints_tv(
    records: list[dict[str, Any]],
    model_key: str,
    margin: float,
    resamples: int,
    seed: int,
    prior_condition: str = "C6",
    regime: str | None = None,
) -> EquivalenceOutcome:
    """The same comparison as :func:`prior_times_constraints`, in total variation.

    The KL version is what the pre-registration froze, and its *verdict* is sound: for any
    floor small enough to represent "the constraints exclude this", a readout with two
    thirds of its mass outside the consistent set is nowhere near 0.15 bits.

    Its *magnitude* is not interpretable, and should not be quoted as one. The reported
    value is dominated by ``m * log2(m / floor)`` where ``m`` is the mass outside the
    consistent set: at the measured m = 0.674, a floor of 1e-3 gives 6.3 bits, 1e-6 gives
    13.1, and 1e-9 gives 19.8. The number describes the floor.

    Total variation has no floor to choose, is bounded in [0, 1], and answers the same
    question. It is reported alongside so the size of the effect is readable and not only
    its sign.
    """
    prior = _index(records, model_key, prior_condition, regime=regime)

    def statistic(a: dict[str, Any], b: dict[str, Any]) -> float | None:
        consistent = a["consistent_set"]
        if len(consistent) >= len(a["conditional"]):
            return None
        mass = math.fsum(b["conditional"][i] for i in consistent)
        if mass <= 0.0:
            return None
        keep = set(consistent)
        reweighted = [
            (b["conditional"][i] / mass if i in keep else 0.0) for i in range(len(b["conditional"]))
        ]
        return metrics.total_variation(a["conditional"], reweighted)

    grouped, dropped = _paired_by_game(
        _index(records, model_key, "C0", regime=regime), prior, statistic
    )
    return _bounded_or_unrun(
        grouped,
        dropped,
        margin,
        resamples,
        seed,
        name=f"T10_tv_prior_times_constraints_vs_{prior_condition}",
        tier=2,
        description=(
            f"TV(C0 readout, {prior_condition} prior restricted to the consistent set) — "
            "the floor-free companion to the pre-registered KL"
        ),
    )


def override_framing_contrast(
    records: list[dict[str, Any]], model_key: str, resamples: int, seed: int
) -> dict[str, tuple[Interval, int]]:
    """TV between an override readout and a neutral readout, **per condition and probe**.

    Tier 3. Keeping the conditions apart is a correctness requirement, not a presentational
    choice. Keying override records by ``(game, probe)`` alone would collapse the four records
    sharing each key to whichever came last, and compare every neutral record in the dataset
    against that one survivor -- a pooled statistic reported under a per-condition name.

    **Override probes are also kept apart from each other**, for the same reason one level
    down. `R0` carries Luo et al.'s Number Guessing clause (their Listing 1) and `R0S` the
    stronger Entity Guessing one (Listing 3); the two are different instruments and pooling
    them would report their average as though it were one measurement.

    The clause sits in the system prompt from the first turn, so this measures the instrument
    as a whole -- clause plus probe -- not the probe wording alone. That is the fair unit,
    since their design specifies the clause exactly that way.

    Returns:
        ``"<condition>/<override readout key>"`` to ``(interval, n_games)``.
    """
    out: dict[str, tuple[Interval, int]] = {}
    keyed = {
        (r["condition"], r["readout_key"])
        for r in records
        if r["readout_framing"] == "sudo_override" and r["model_key"] == model_key
    }
    for condition, readout_key in sorted(keyed):
        override = _index(records, model_key, condition, framing="sudo_override")
        neutral = _index(records, model_key, condition, framing="neutral")
        # Each override record is compared against every neutral paraphrase at the same
        # state, so paraphrase variation is inside the comparison rather than beside it.
        by_state: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for (game, probe, _readout), neut in neutral.items():
            by_state[(game, probe)].append(neut)
        grouped: dict[str, list[float]] = defaultdict(list)
        for (game, probe, readout), over in override.items():
            if readout != readout_key:
                continue
            grouped[game].extend(
                metrics.total_variation(neut["conditional"], over["conditional"])
                for neut in by_state.get((game, probe), [])
            )
        grouped = {g: v for g, v in grouped.items() if v}
        if not grouped:
            continue
        out[f"{condition}/{readout_key}"] = (
            cluster_bootstrap(
                _sorted_clusters(grouped), lambda a: float(a.mean()), resamples, seed
            ),
            len(grouped),
        )
    return out


def _robustness_arms(
    report: Tier23Report,
    records: list[dict[str, Any]],
    model_key: str,
    resamples: int,
    seed: int,
) -> None:
    """Elicitation robustness (Tier 2) and the Luo truncation comparison (Tier 3)."""
    report.paraphrase = paraphrase_agreement(records, model_key, resamples, seed)
    if report.paraphrase is None:
        report.notes.append("Paraphrase agreement UNRUN: too few states with two paraphrases")
    report.drift = turn_drift(records, model_key, resamples, seed)
    if report.drift is None:
        report.notes.append("Turn drift UNRUN: no early/late pairs at a matched paraphrase")
    # **Each override probe is reported separately.** `R0` and `R0S` share a framing and are
    # two different instruments -- Luo's Listing 1 clause and Listing 3's stronger one -- so a
    # single `sudo_override` row reported their average as one measurement. The neutral
    # paraphrases are genuinely interchangeable and stay pooled.
    for label, kwargs in (
        ("R0", {"framing": "sudo_override", "readout_key": "R0"}),
        ("R0S", {"framing": "sudo_override", "readout_key": "R0S"}),
        ("neutral", {"framing": "neutral"}),
    ):
        try:
            report.truncation[label] = truncation_effect(
                records, model_key, resamples, seed, **kwargs
            )
        except ValueError as exc:
            report.notes.append(f"Tier-3 truncation comparison ({label}) unavailable: {exc}")


def analyse(
    records: list[dict[str, Any]],
    model_key: str,
    thresholds: dict[str, float],
    resamples: int,
    seed: int,
) -> Tier23Report:
    """Compute every Tier-2 and Tier-3 outcome for one model.

    Regimes are analysed separately, never pooled: Regime D contributes 6 observations per
    game and Regime U contributes 16, so pooling silently weights a U game 2.7x a D game.
    """
    report = Tier23Report(model_key=model_key)
    for regime in ("D", "U"):
        for name, fn, margin in (
            ("commitment_framing", commitment_framing_effect, thresholds["tost_tv_margin"]),
            ("prior_times_constraints", prior_times_constraints, thresholds["tost_kl_margin_bits"]),
            (
                "prior_times_constraints_tv",
                prior_times_constraints_tv,
                thresholds["tost_tv_margin"],
            ),
        ):
            try:
                outcome = fn(records, model_key, margin, resamples, seed, regime=regime)
            except ValueError as exc:
                report.notes.append(f"{name} unavailable for regime {regime}: {exc}")
                continue
            if outcome.n_games < MIN_CLUSTERS_FOR_BOOTSTRAP:
                report.notes.append(
                    f"{name}[{regime}] UNRUN: {outcome.n_games} matched games "
                    f"({outcome.dropped} pairs dropped as undefined); too few to bootstrap"
                )
                continue
            outcome.name = f"{outcome.name}[{regime}]"
            report.equivalences.append(outcome)

    _robustness_arms(report, records, model_key, resamples, seed)

    try:
        report.override_contrast = override_framing_contrast(records, model_key, resamples, seed)
    except ValueError as exc:
        report.notes.append(f"Tier-3 override contrast unavailable: {exc}")
    if not report.override_contrast:
        report.notes.append("No Tier-3 override records present; Luo replication UNRUN.")
    return report


def _render_robustness(report: Tier23Report) -> list[str]:
    """Render the elicitation-robustness and Luo-truncation blocks."""
    out: list[str] = []
    if report.paraphrase is not None or report.drift is not None:
        out += [
            "**Tier 2 — elicitation robustness.** Paraphrase agreement is mean pairwise",
            "`1 - TV` across the neutral paraphrases at one state; the override probe is",
            "excluded, since it carries a system clause the others do not and pooling it",
            "would report a framing effect as paraphrase noise. Turn drift is TV between the",
            "early and late readouts at the same state and paraphrase — it *should* move,",
            "since the constraints entering the context are new information.",
            "",
            "Agreement is reported against its chance baseline: a concentrated readout",
            "produces high agreement with no stability whatsoever, so the number to read is",
            "the gap between paraphrases and what two draws from a *single* paraphrase",
            "would already show (Lanham et al. 2023, App. B).",
            "",
            "| | estimate | 95% upper bound |",
            "|---|---|---|",
        ]
        if report.paraphrase is not None:
            tv, observed, chance = report.paraphrase
            out += [
                f"| paraphrase agreement, mean 1 - TV (C0) | {tv.estimate:.4f} | "
                f"[{tv.low:.4f}, {tv.high:.4f}] |",
                f"| — as draw agreement, observed | {observed.estimate:.4f} | "
                f"[{observed.low:.4f}, {observed.high:.4f}] |",
                f"| — chance baseline (two draws, one paraphrase) | {chance.estimate:.4f} | "
                f"[{chance.low:.4f}, {chance.high:.4f}] |",
            ]
        if report.drift is not None:
            d = report.drift
            out.append(
                f"| turn drift, early → late (C0) | {d.estimate:.4f} | "
                f"[{d.low:.4f}, {d.high:.4f}] |"
            )
        out.append("")
    if report.truncation:
        out += [
            "**Tier 3 — what Luo et al.'s top-20 truncation contributes.** Their pipeline",
            "keeps the top 20 vocabulary logits and assigns -9999 to the rest, so a candidate",
            "that drops out of the window does not become unlikely, it becomes impossible —",
            "and a KL against a zero is unbounded. The same early→late KL is computed both",
            "ways on the same states. `sudo_override` is their own probe, which is the row",
            "that bears on their reported numbers; `neutral` is ours, reported beside it.",
            "",
            "| probe | states | a candidate truncated | KL literally infinite | mean KL, "
            "full support | mean KL, truncated |",
            "|---|---|---|---|---|---|",
        ]
        for framing, t in sorted(report.truncation.items()):
            full = t.get("mean_kl_full_support")
            trunc = t.get("mean_kl_luo_truncated")
            out.append(
                f"| {framing} | {t.get('states', 0)} | "
                f"{t.get('states_with_a_truncated_candidate', 0)} | "
                f"{t.get('states_with_infinite_truncated_kl', 0)} | "
                + (f"{full:.4f} bits" if isinstance(full, float) else "—")
                + " | "
                + (f"{trunc:.4f} bits" if isinstance(trunc, float) else "—")
                + " |"
            )
        out.append("")
        out.append(
            "The means exclude the infinite cases, which are counted instead: a mean "
            "containing an infinity is infinite, and the count says more."
        )
        out.append("")
    return out


def render(reports: list[Tier23Report]) -> str:
    """Render Tier-2 and Tier-3 outcomes as Markdown."""
    lines = [
        "# Experiment 1 — Tier-2 (mechanism) and Tier-3 (Luo replication)",
        "",
        "**These do not bear on Tier 1.** Tier 1 rests on state identity; a failure here is a",
        "finding about the readout distribution, not about the causal demonstration.",
        "",
        "Regimes are reported separately. Equivalence is a **one-sided upper bound** on a",
        "non-negative distance, not a symmetric interval — see `stats.equivalence_upper_bound`.",
        "",
        "**T10's KL magnitude is not interpretable; its verdict is.** The value is dominated",
        "by `m · log2(m / floor)`, where `m` is the readout mass falling outside the",
        "constraint-consistent set and `floor` is the probability assigned to an excluded",
        "candidate. At the measured m ≈ 0.67, a floor of 1e-3 gives 6.3 bits and 1e-9 gives",
        "19.8 — the number describes the floor. The verdict is robust for any floor small",
        'enough to mean "excluded", and `T10_tv` reports the same comparison in total',
        "variation, which has no floor to choose and is bounded in [0, 1].",
        "",
    ]
    for report in reports:
        lines.append(f"## {report.model_key}")
        lines.append("")
        if report.equivalences:
            lines.append(
                "| Test | Tier | n games | dropped | estimate | 95% upper bound | margin | within |"
            )
            lines.append("|---|---|---|---|---|---|---|---|")
            lines.extend(
                f"| {o.name} | {o.tier} | {o.n_games} | {o.dropped} | "
                f"{o.interval.estimate:.4f} | [{o.interval.low:.4f}, {o.interval.high:.4f}] | "
                f"{o.margin} | {'YES' if o.equivalent else 'NO'} |"
                for o in report.equivalences
            )
            lines.append("")
        if report.override_contrast:
            lines.append(
                "**Tier 3 — Luo override framing, per condition and per probe.** TV "
                "between the SUDO-override readout and the neutral readout at the *same "
                "condition and state*. Pooling conditions here produced a retracted "
                "finding. `R0` is their Number Guessing clause (Listing 1), which is the "
                "task replicated here; `R0S` is the stronger Entity Guessing clause "
                "(Listing 3) run on the same scenario, so the pair isolates instruction "
                "strength from override framing. They are never pooled."
            )
            lines.append("")
            lines.append("| Condition / override probe | n games | mean TV | 95% upper bound |")
            lines.append("|---|---|---|---|")
            lines.extend(
                f"| {c} | {n} | {i.estimate:.4f} | [{i.low:.4f}, {i.high:.4f}] |"
                for c, (i, n) in sorted(report.override_contrast.items())
            )
            lines.append("")
        lines.extend(_render_robustness(report))
        for note in report.notes:
            lines.append(f"> {note}")
            lines.append("")
    return "\n".join(lines)


#: Luo et al. 2026 rank their candidate logits and keep the top 20, assigning -9999 to the
#: rest before renormalising. The constant is theirs; it is reproduced rather than chosen.
LUO_TOP_K = 20

#: The log-probability Luo et al. assign to a truncated candidate. Not a floor in any
#: statistical sense -- it is a sentinel that renormalises to essentially zero, which is
#: precisely why it can make a turn-to-turn KL diverge.
LUO_TRUNCATION_LOGIT = -9999.0


def truncation_effect(
    records: list[dict[str, Any]],
    model_key: str,
    resamples: int,
    seed: int,
    framing: str | None = None,
    readout_key: str | None = None,
) -> dict[str, float | int]:
    """How much of Luo et al.'s turn-to-turn instability is their truncation?

    Tier 3. Their pipeline keeps the top 20 *vocabulary* logits and assigns -9999 to
    everything else. A candidate that drops out of the vocabulary top-20 between two turns
    therefore does not merely become unlikely -- it becomes impossible, and a KL against a
    zero is unbounded. Reported instability then measures the sentinel, not the model.

    Our records carry the top-64 vocabulary tokens per probe, so which candidates their
    truncation would have discarded is directly checkable rather than a matter of argument.
    The same early-to-late KL is computed both ways on the same states.

    Args:
        records: All records.
        model_key: Model to analyse.
        resamples: Bootstrap resamples.
        seed: Bootstrap seed.
        framing: Restrict to one readout framing. Their KL is computed on **their** probe's
            distributions, so pooling their override readout with our neutral paraphrases
            would report an average across two instruments as though it were one.
        readout_key: Restrict to one probe. **A framing is not an instrument**, and this is
            the second half of the same argument: `R0` and `R0S` both carry
            `sudo_override`, but they are Luo's Listing 1 clause and Listing 3's stronger
            one. Filtering on framing alone pooled them, and the published F15 magnitudes
            were their average -- 3.684 against 3.511 bits for Gemma, 5.087 against 4.572
            for Qwen, with two truncated candidates that all came from `R0S` rather than
            from the probe the row names.

    Returns:
        Counts and the paired KL means, full support against Luo-truncated.
    """
    early = _index(records, model_key, "C0", regime="D", framing=framing, readout_key=readout_key)
    paired: dict[str, list[tuple[float, float]]] = defaultdict(list)
    affected = 0
    total = 0
    for (game, probe, readout), record in early.items():
        if probe != "early":
            continue
        partner = next(
            (r for (g, p, rk), r in early.items() if (g, rk) == (game, readout) and p == "late"),
            None,
        )
        if partner is None:
            continue
        total += 1
        full = metrics.kl_divergence_bits(partner["conditional"], record["conditional"])
        kept_early = _luo_kept(record)
        kept_late = _luo_kept(partner)
        if not (all(kept_early) and all(kept_late)):
            affected += 1
        truncated = metrics.kl_divergence_bits(
            _luo_renormalise(partner, kept_late), _luo_renormalise(record, kept_early)
        )
        paired[game].append((full, truncated))

    # An infinite truncated KL is the headline, not a nuisance: it is what -9999 does when a
    # candidate leaves the window, and it is unbounded rather than merely large. It is
    # counted and reported, and excluded from the mean -- a mean containing an infinity is
    # infinite, which conveys less than the count does.
    infinite = sum(1 for v in paired.values() for _, b in v if not math.isfinite(b))
    finite = {game: [(a, b) for a, b in v if math.isfinite(b)] for game, v in paired.items()}
    finite = {game: v for game, v in finite.items() if v}

    out: dict[str, float | int] = {
        "states": total,
        "states_with_a_truncated_candidate": affected,
        "states_with_infinite_truncated_kl": infinite,
    }
    if len(finite) >= MIN_CLUSTERS_FOR_BOOTSTRAP:
        out["mean_kl_full_support"] = cluster_bootstrap(
            [[a for a, _ in v] for v in finite.values()],
            lambda a: float(a.mean()),
            resamples,
            seed,
        ).estimate
        out["mean_kl_luo_truncated"] = cluster_bootstrap(
            [[b for _, b in v] for v in finite.values()],
            lambda a: float(a.mean()),
            resamples,
            seed,
        ).estimate
        out["games"] = len(finite)
    return out


def _luo_kept(record: dict[str, Any]) -> list[bool]:
    """Which candidates survive Luo et al.'s top-20 vocabulary truncation.

    Decided from the log-probabilities rather than from token ids: `topk_logprobs` is sorted
    descending over the vocabulary, so a candidate is inside the top 20 exactly when its own
    log-probability is at least the 20th largest. That needs no extra field and is exact.

    When fewer than 20 top tokens were recorded, nothing is truncated -- the recorded window
    does not reach the cut, so claiming a candidate fell outside it would be an inference
    from missing data.
    """
    top = record["topk_logprobs"]
    if len(top) < LUO_TOP_K:
        return [True] * len(record["candidate_logprobs"])
    cut = top[LUO_TOP_K - 1]
    return [lp >= cut for lp in record["candidate_logprobs"]]


def _luo_renormalise(record: dict[str, Any], kept: list[bool]) -> list[float]:
    """Apply the truncation and renormalise, exactly as their pipeline would.

    A discarded candidate gets ``exp(-9999)``, which underflows to zero -- so this is where
    an unbounded KL comes from. The floor is kept explicit rather than replaced with a small
    positive number: substituting a gentler floor would measure a method nobody used.
    """
    raw = [
        math.exp(lp) if keep else math.exp(LUO_TRUNCATION_LOGIT)
        for lp, keep in zip(record["candidate_logprobs"], kept, strict=True)
    ]
    total = math.fsum(raw)
    if total <= 0.0:
        # Every candidate truncated. Returning a uniform distribution turns the most extreme
        # instance of the finding -- a readout with no surviving mass at all -- into a KL of
        # exactly zero, and hides it in the mean rather than counting it as dropped.
        raise CorruptRecordSetError(
            "every candidate was truncated by Luo et al.'s top-20 rule, so the renormalised "
            "distribution is undefined; this record must be counted as dropped, not scored"
        )
    return [x / total for x in raw]


def paraphrase_agreement(
    records: list[dict[str, Any]], model_key: str, resamples: int, seed: int
) -> tuple[Interval, Interval, Interval] | None:
    """Mean pairwise ``1 - TV`` across the neutral paraphrases at one state.

    Tier 2. Every paraphrase branches from the same captured state and asks the same
    question in different words, so disagreement between them is elicitation sensitivity
    rather than anything about a commitment. A readout that moved substantially with wording
    would put a ceiling on how much any single paraphrase can be said to measure.

    The Luo override probe is excluded: it carries a system clause the neutral paraphrases do
    not, so pooling it would report a framing effect as paraphrase noise.

    Returns:
        ``(mean 1 - TV, observed draw agreement, chance baseline)``, or None if there are
        too few states. The last two are what make the first interpretable: a concentrated
        readout produces high agreement with no stability whatsoever, so the number to read
        is the gap between the observed cross-paraphrase agreement and the agreement two
        draws from a *single* paraphrase would already show (Lanham et al. 2023, App. B).
    """
    grouped: dict[str, list[list[float]]] = defaultdict(list)
    for record in records:
        if (
            record["model_key"] != model_key
            or record["sampler_role"] != "none"
            or record["readout_framing"] != "neutral"
            or record["condition"] != "C0"
        ):
            continue
        grouped[f"{record['game_id']}|{record['probe_point']}"].append(record["conditional"])
    tv_by_game: dict[str, list[float]] = defaultdict(list)
    observed_by_game: dict[str, list[float]] = defaultdict(list)
    chance_by_game: dict[str, list[float]] = defaultdict(list)
    for key, distributions in grouped.items():
        if len(distributions) < metrics.MIN_DISTRIBUTIONS_FOR_AGREEMENT:
            continue
        game = key.split("|", 1)[0]
        tv_by_game[game].append(metrics.mean_pairwise_agreement(distributions))
        pairs = [
            metrics.draw_agreement(distributions[i], distributions[j])
            for i in range(len(distributions))
            for j in range(i + 1, len(distributions))
        ]
        observed_by_game[game].append(math.fsum(pairs) / len(pairs))
        chance_by_game[game].append(
            math.fsum(metrics.iid_agreement_baseline(d) for d in distributions) / len(distributions)
        )
    if len(tv_by_game) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return None
    tv, observed, chance = (
        cluster_bootstrap(_sorted_clusters(g), lambda a: float(a.mean()), resamples, seed)
        for g in (tv_by_game, observed_by_game, chance_by_game)
    )
    return tv, observed, chance


def turn_drift(
    records: list[dict[str, Any]], model_key: str, resamples: int, seed: int
) -> Interval | None:
    """TV between the early and late readouts at the same state and paraphrase.

    Tier 2. Measures how far the readout moves as the scripted questions accumulate. Under
    the paper's reading it should move: the constraints entering the context are new
    information, and a distribution that ignored them would be the surprising result.
    """
    early = _index(records, model_key, "C0", regime="D", framing="neutral")
    by_game: dict[str, list[float]] = defaultdict(list)
    for (game, probe, readout), record in early.items():
        if probe != "early":
            continue
        partner = next(
            (r for (g, p, rk), r in early.items() if (g, rk) == (game, readout) and p == "late"),
            None,
        )
        if partner is not None:
            by_game[game].append(
                metrics.total_variation(record["conditional"], partner["conditional"])
            )
    if len(by_game) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return None
    return cluster_bootstrap(_sorted_clusters(by_game), lambda a: float(a.mean()), resamples, seed)
