# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""The bare-value robustness arm (Tier 2).

Every Tier-1 number is measured over single-token **indices** 0-9, which are pointers into a
list. F6 shows that costs something real: mass over index positions is strongly structured,
with 0.019 on the first and last positions against 0.160 in the middle. That is a fact about
positions, and no care with the index scheme separates it from a fact about targets.

This module analyses the arm that removes the pointer. Options are shown as fixed-width
two-digit values with no index labels, and the readout is scored over all 100 values by a
prefix trie. Three questions become answerable:

* **Does the near-chance C0 readout survive?** If it does, F1 is not an artefact of indices.
* **Does C1 still recover an injected target?** Without this the arm proves nothing: a null
  in an answer space where nothing can be recovered is not evidence of absence.
* **Does the positional structure persist?** In the index arm, position *is* the answer. Here
  it is not, so any remaining effect of list position on the value chosen is a positional
  prior that survives the removal of the pointer -- and any effect that disappears was the
  pointer.

**Tier 2 throughout.** Nothing here can disturb Tier 1, which rests on state identity.
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
    binomial_gate,
    cluster_bootstrap,
)

#: The arm is defined by its readout format, not by a key prefix: a record belongs here
#: because its answer space was values, which is what `format = "bare_value"` declares.
BARE_READOUT_PREFIX = "B"


@dataclass(slots=True)
class BareValueReport:
    """Bare-value outcomes for one model."""

    model_key: str
    states: int = 0
    #: Mean probability the model answers with a fixed-width number at all, by condition.
    numeric_mass: dict[str, Interval] = field(default_factory=dict)
    #: Of that, the share landing on a value the model was actually shown. The index arm
    #: cannot ask this: there, every candidate is an option.
    option_share: dict[str, Interval] = field(default_factory=dict)
    #: Mean readout mass on the constraint-consistent value, by condition.
    consistent_mass: dict[str, Interval] = field(default_factory=dict)
    #: Mean entropy over the ten offered values, by condition.
    entropy: dict[str, float] = field(default_factory=dict)
    #: C1 recovery in the value answer space -- the sensitivity gate for this arm.
    recovery: tuple[int, int] = (0, 0)
    recovery_passed: bool = False
    #: Mean conditional probability by LIST POSITION under C0, comparable to F6.
    position_profile: list[float] = field(default_factory=list)
    #: Edge positions versus interior, the statistic F6 reports.
    edge_mass: float = math.nan
    interior_mass: float = math.nan
    notes: list[str] = field(default_factory=list)


def _sorted_clusters(groups: dict[Any, list[float]]) -> list[list[float]]:
    """Clusters in a deterministic order.

    The point estimate does not depend on the order clusters are supplied in; the percentile
    bounds do. Insertion order follows the order records were read, so a reader who concatenates
    the input files differently gets different interval bounds. `utility._cluster` already sorts;
    this does the same for every other call site.
    """
    return [groups[k] for k in sorted(groups)]


def bare_records(records: list[dict[str, Any]], model_key: str) -> list[dict[str, Any]]:
    """Records from the bare-value arm for one model."""
    return [
        r
        for r in records
        if r["model_key"] == model_key
        and r["sampler_role"] == "none"
        and str(r["readout_key"]).startswith(BARE_READOUT_PREFIX)
    ]


def _by_game(records: list[dict[str, Any]], value: Any) -> dict[str, list[float]]:
    """Group a per-record statistic by game, which is what the bootstrap resamples."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[record["game_id"]].append(value(record))
    return grouped


def _interval(grouped: dict[str, list[float]], resamples: int, seed: int) -> Interval | None:
    if len(grouped) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return None
    return cluster_bootstrap(_sorted_clusters(grouped), lambda a: float(a.mean()), resamples, seed)


def analyse(
    records: list[dict[str, Any]],
    model_key: str,
    thresholds: dict[str, float],
    resamples: int,
    seed: int,
) -> BareValueReport:
    """Compute every bare-value outcome for one model.

    Args:
        records: All records, for any model and any arm.
        model_key: Which model to analyse.
        thresholds: Pre-registered thresholds, keyed by test name.
        resamples: Cluster-bootstrap resamples.
        seed: Cluster-bootstrap seed.

    Returns:
        The model's report.
    """
    rows = bare_records(records, model_key)
    # Distinct states, not records: several readouts share one captured state, and `tier1`'s
    # own `states` counts `(game_id, probe_point)` for exactly this reason. Publishing a record
    # count under the name "states" overstated the design by a factor of two.
    report = BareValueReport(
        model_key=model_key,
        states=len({(r["condition"], r["game_id"], r["probe_point"]) for r in rows}),
    )
    if not rows:
        report.notes.append("No bare-value records present; this arm is UNRUN.")
        return report

    # Keyed on condition AND probe point. Pooling them averages the contrast the whole
    # argument rests on: at `early` no question has been asked and the readout is at chance,
    # at `late` the constraints are in context. A pooled C0 number is the mean of those two
    # and describes neither.
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in rows:
        by_condition[f"{record['condition']} {record['probe_point']}"].append(record)

    _per_condition(report, by_condition, resamples, seed)

    # --- the sensitivity gate, restated in the value answer space ---
    c1 = [r for r in rows if r["condition"] == "C1"]
    recovered = sum(
        1
        for r in c1
        if r["injected_index"] is not None and _argmax_position(r) == int(r["injected_index"])
    )
    gate = binomial_gate(recovered, len(c1), thresholds["recovery_acc_min"], "min")
    report.recovery = (recovered, len(c1))
    report.recovery_passed = gate.passed
    if not gate.passed:
        report.notes.append(
            "C1 recovery does not clear the sensitivity threshold in the value answer "
            "space. Read every other number here as uninterpretable rather than null: an "
            "arm that cannot recover a target that IS present says nothing about absence."
        )

    # --- F6 restated where position is not the answer ---
    c0 = [r for r in rows if r["condition"] == "C0"]
    if c0:
        # Profiled over LIST POSITION, not over value. The ten options differ from game to
        # game, so a profile keyed on the value would average ten different things; F6's
        # statistic is about where in the list the mass goes.
        n_options = len(c0[0]["option_values"])
        totals = [0.0] * n_options
        for record in c0:
            share = _option_share(record)
            if share <= 0.0:
                continue
            for slot, position in enumerate(option_positions(record)):
                totals[slot] += record["conditional"][position] / share
        report.position_profile = [t / len(c0) for t in totals]
        report.edge_mass = (report.position_profile[0] + report.position_profile[-1]) / 2.0
        interior = report.position_profile[1:-1]
        report.interior_mass = math.fsum(interior) / len(interior) if interior else math.nan
    return report


def option_positions(record: dict[str, Any]) -> list[int]:
    """Positions in ``candidates`` of the values the model was actually shown.

    Candidates are every fixed-width number, sorted, so a candidate's position is its
    value -- but that is a property of this arm's construction, not something to assume.
    Looking the options up by name keeps the analysis correct if the candidate ordering
    ever changes.
    """
    where = {name: i for i, name in enumerate(record["candidates"])}
    return [where[v] for v in record["option_values"]]


def _option_share(record: dict[str, Any]) -> float:
    """Share of the numeric answer mass that lands on an offered value."""
    return math.fsum(record["conditional"][i] for i in option_positions(record))


def _per_condition(
    report: BareValueReport,
    by_condition: dict[str, list[dict[str, Any]]],
    resamples: int,
    seed: int,
) -> None:
    """Fill the per-condition mass and entropy tables."""
    for condition, group in sorted(by_condition.items()):
        numeric = _interval(_by_game(group, lambda r: r["candidate_mass"]), resamples, seed)
        if numeric is not None:
            report.numeric_mass[condition] = numeric
        share = _interval(_by_game(group, _option_share), resamples, seed)
        if share is not None:
            report.option_share[condition] = share
        consistent = _interval(
            _by_game(
                group,
                lambda r: metrics.consistent_mass(r["conditional"], r["consistent_set"]),
            ),
            resamples,
            seed,
        )
        if consistent is not None:
            report.consistent_mass[condition] = consistent
        report.entropy[condition] = math.fsum(r["entropy_bits"] for r in group) / len(group)


def _argmax_position(record: dict[str, Any]) -> int:
    """List position of the highest-scoring offered value."""
    logprobs = record["candidate_logprobs"]
    return max(range(len(logprobs)), key=lambda i: logprobs[i])


def _cell(interval: Interval | None) -> str:
    """Render an interval for a Markdown table, or an em dash when it could not be formed."""
    if interval is None:
        return "—"
    return f"{interval.estimate:.4f} [{interval.low:.4f}, {interval.high:.4f}]"


def render(reports: list[BareValueReport]) -> str:
    """Render the bare-value outcomes as Markdown."""
    lines = [
        "# Experiment 1 — bare-value robustness arm (Tier 2)",
        "",
        "Options shown as fixed-width two-digit values with **no index labels**; the readout",
        "is scored over all 100 values by a prefix trie. `option mass` is the probability the",
        "model puts on answering with one of the ten values it was actually shown — the",
        "question the index arm cannot pose, since there every candidate is an option.",
        "",
        "**Tier 2. This cannot disturb Tier 1**, which rests on state identity and holds in",
        "either answer space.",
        "",
    ]
    for report in reports:
        lines.append(f"## {report.model_key}")
        lines.append("")
        if not report.states:
            lines.extend(f"> {note}" for note in report.notes)
            lines.append("")
            continue
        lines.append(f"States: {report.states}")
        lines.append("")
        hits, trials = report.recovery
        verdict = "PASS" if report.recovery_passed else "FAIL"
        lines.append(
            f"**Sensitivity (C1 recovery over values): {hits}/{trials} — {verdict}.** "
            "Without this, nothing else on this page is interpretable."
        )
        lines.append("")
        lines.append(
            "| Condition | answers with a number | of that, an offered value | "
            "mass on the consistent value | entropy (bits) |"
        )
        lines.append("|---|---|---|---|---|")
        lines.extend(
            f"| {condition} | {_cell(report.numeric_mass.get(condition))} | "
            f"{_cell(report.option_share.get(condition))} | "
            f"{_cell(report.consistent_mass.get(condition))} | "
            f"{report.entropy.get(condition, math.nan):.4f} |"
            for condition in sorted(set(report.numeric_mass) | set(report.consistent_mass))
        )
        lines.append("")
        if report.position_profile:
            lines.append("Mean conditional probability by **list position** under C0 — the F6")
            lines.append("statistic, measured where position is not the answer:")
            lines.append("")
            lines.append(
                "| position | "
                + " | ".join(str(i) for i in range(len(report.position_profile)))
                + " |"
            )
            lines.append("|---" * (len(report.position_profile) + 1) + "|")
            lines.append(
                "| mean p | " + " | ".join(f"{p:.3f}" for p in report.position_profile) + " |"
            )
            lines.append("")
            lines.append(
                f"Edge (first and last) {report.edge_mass:.3f} against interior "
                f"{report.interior_mass:.3f}, a ratio of "
                f"{report.edge_mass / report.interior_mass:.2f}. Compare the same ratio in "
                "`RESULTS.md`, computed on the index arm of this run."
            )
            lines.append("")
        for note in report.notes:
            lines.append(f"> {note}")
            lines.append("")
    return "\n".join(lines)
