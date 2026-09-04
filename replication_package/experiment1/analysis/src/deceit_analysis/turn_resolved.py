# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Luo et al.'s turn-resolved metrics, with the positive control they did not have.

Their headline **Drift Rate** is `#changes / T` over consecutive dialogue turns, and their
**KL Divergence** is `D_KL(P_t || P_{t-1})` between adjacent turns. Neither is expressible at
two probe points: those give only the **Branch Drift Rate** of their Appendix C,
`E[1(p_T != p_0)]`, which is a lower bound on how often the target changed and is silent
about *when* it changed.

With the full six-point trajectory both are computable exactly as defined, and the C1/C2
conditions supply what their design cannot: a run in which a target genuinely is present, so
"how much does the target drift" has a measurable floor.

The *when* matters for our own account and can falsify it. If there is no target and the
readout is prior reweighted by whatever constraints are in context, drift should track
information arriving -- frequent while the answers are still narrowing, rarer once they have
narrowed. A drift rate flat across turns would be evidence against that reading, and two
probe points cannot tell the difference.

**Tier 2.** Tier 1 rests on state identity and does not depend on turn resolution.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from deceit_analysis import metrics
from deceit_analysis.stats import MIN_CLUSTERS_FOR_BOOTSTRAP, Interval, cluster_bootstrap

#: The trajectory, in order. `early` and `late` come from the Tier-1 file; the rest from the
#: turn-resolved stage. They are joined rather than re-measured -- same games, same seed.
TRAJECTORY = ("early", "turn1", "turn2", "turn3", "turn4", "late")


@dataclass(slots=True)
class TurnReport:
    """Turn-resolved outcomes for one model."""

    model_key: str
    trajectories: int = 0
    #: Their headline metric, `#changes / T`, by condition.
    drift_rate: dict[str, Interval] = field(default_factory=dict)
    #: Their `Once D.R.`: did the target change at any point.
    once_drift: dict[str, Interval] = field(default_factory=dict)
    #: Their Appendix C Branch Drift Rate, `1(p_T != p_0)`, for comparison with the
    #: two-point estimate the rest of this package reports.
    branch_drift: dict[str, Interval] = field(default_factory=dict)
    #: Mean `D_KL(P_t || P_{t-1})` at each step, by condition. Position i is the step from
    #: `TRAJECTORY[i]` to `TRAJECTORY[i + 1]`.
    step_kl: dict[str, list[float]] = field(default_factory=dict)
    #: Fraction of trajectories whose target changes at each step, by condition.
    step_change: dict[str, list[float]] = field(default_factory=dict)
    #: Mean mass on the C4 distractor at each probe point, and on the constraint-consistent
    #: answer beside it. Separates "the model retained the old target" from "the old target
    #: was the most available candidate until something ruled it out".
    distractor_mass: list[float] = field(default_factory=list)
    consistent_mass_c4: list[float] = field(default_factory=list)
    #: How often a narrowing step excluded the distractor outright.
    distractor_excluded: tuple[int, int] = (0, 0)
    #: Drift split by whether the step's question actually narrowed the candidate set:
    #: ``{condition: (informative rate, n, filler rate, n)}``. This is the discriminating
    #: test -- a filler turn adds a turn and no information, so under "the belief drifts over
    #: time" it should drift like any other, and under "the readout tracks constraints
    #: arriving" it should not.
    drift_by_information: dict[str, tuple[float, int, float, int]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _sorted_clusters(groups: dict[Any, list[float]]) -> list[list[float]]:
    """Clusters in a deterministic order.

    The point estimate does not depend on the order clusters are supplied in; the percentile
    bounds do. Insertion order follows the order records were read, so a reader who concatenates
    the input files differently gets different interval bounds. `utility._cluster` already sorts;
    this does the same for every other call site.
    """
    return [groups[k] for k in sorted(groups)]


def _distractor_exclusions(trajectory: list[dict[str, Any]]) -> tuple[int, int]:
    """Count narrowing steps that excluded the distractor, against those that did not."""
    excluded = kept = 0
    for before, after in pairwise(trajectory):
        if _narrowed(before, after) is not True:
            continue
        index = after.get("distractor_index")
        running = after.get("running_consistent_set")
        if index is None or running is None:
            continue
        if index in running:
            kept += 1
        else:
            excluded += 1
    return excluded, kept


def _distractor_trajectory(report: TurnReport, group: list[list[dict[str, Any]]]) -> None:
    """Trace the C4 distractor's mass along the trajectory.

    The two-point grid pools `early` and `late`, and for the distractor those are very
    different states: at `early` nothing has been asked, so the previous game's index is
    simply the most available candidate in context. Pooling them reports a mean of the two
    and reads as though the model held the old target throughout.

    Also counts how often a narrowing step *excludes* the distractor. C4 places it outside
    the consistent set by construction, so a constraint that narrows will usually rule it
    out -- and whether its mass then falls is what separates prior mass from a belief.
    """
    if not group:
        return
    points = len(TRAJECTORY)
    dist = [[] for _ in range(points)]  # type: list[list[float]]
    cons = [[] for _ in range(points)]  # type: list[list[float]]
    excluded = kept = 0
    for trajectory in group:
        for i, record in enumerate(trajectory):
            index = record.get("distractor_index")
            if index is not None:
                dist[i].append(record["conditional"][index])
            cons[i].append(math.fsum(record["conditional"][j] for j in record["consistent_set"]))
        gone, stayed = _distractor_exclusions(trajectory)
        excluded += gone
        kept += stayed
    report.distractor_mass = [math.fsum(v) / len(v) if v else math.nan for v in dist]
    report.consistent_mass_c4 = [math.fsum(v) / len(v) if v else math.nan for v in cons]
    report.distractor_excluded = (excluded, excluded + kept)


def _narrowed(before: dict[str, Any], after: dict[str, Any]) -> bool | None:
    """Did the question between two probe points remove any candidate?

    Reads `running_consistent_set`, the constraints in force at each state. Returns None
    when either record predates that field, so an older file degrades to "not measured"
    rather than to a silent False -- which would count every step as filler and invert the
    result.
    """
    left, right = before.get("running_consistent_set"), after.get("running_consistent_set")
    if left is None or right is None:
        return None
    return len(right) < len(left)


def _argmax(record: dict[str, Any]) -> int:
    logprobs = record["candidate_logprobs"]
    return max(range(len(logprobs)), key=lambda i: logprobs[i])


def build_trajectories(
    records: list[dict[str, Any]], model_key: str
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    """Assemble complete six-point trajectories, keyed by (condition, game, readout).

    Incomplete trajectories are dropped rather than padded: a drift rate over a partial
    trajectory has a different denominator and would not be their metric.
    """
    by_key: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        if (
            record["model_key"] != model_key
            or record["sampler_role"] != "none"
            or record["readout_framing"] != "neutral"
            or record.get("option_values") is not None
            or record["regime"] != "D"
        ):
            continue
        key = (record["condition"], record["game_id"], record["readout_key"])
        by_key[key][record["probe_point"]] = record
    return {
        key: [points[p] for p in TRAJECTORY]
        for key, points in by_key.items()
        if all(p in points for p in TRAJECTORY)
    }


def analyse(records: list[dict[str, Any]], model_key: str, resamples: int, seed: int) -> TurnReport:
    """Compute the turn-resolved metrics for one model.

    Args:
        records: All records, Tier-1 and turn-resolved together.
        model_key: Which model to analyse.
        resamples: Cluster-bootstrap resamples.
        seed: Cluster-bootstrap seed.

    Returns:
        The model's report.
    """
    trajectories = build_trajectories(records, model_key)
    report = TurnReport(model_key=model_key, trajectories=len(trajectories))
    if not trajectories:
        report.notes.append("No complete trajectories; the turn-resolved arm is UNRUN.")
        return report

    steps = len(TRAJECTORY) - 1
    by_condition: dict[str, list[list[dict[str, Any]]]] = defaultdict(list)
    for (condition, _game, _readout), points in trajectories.items():
        by_condition[condition].append(points)

    for condition, group in sorted(by_condition.items()):
        _score_condition(report, condition, group, steps, resamples, seed)
    _distractor_trajectory(report, by_condition.get("C4", []))
    return report


def _score_condition(
    report: TurnReport,
    condition: str,
    group: list[list[dict[str, Any]]],
    steps: int,
    resamples: int,
    seed: int,
) -> None:
    """Score one condition's trajectories into ``report``."""
    informative: list[float] = []
    filler: list[float] = []
    drift_by_game: dict[str, list[float]] = defaultdict(list)
    once_by_game: dict[str, list[float]] = defaultdict(list)
    branch_by_game: dict[str, list[float]] = defaultdict(list)
    step_kl = [[] for _ in range(steps)]  # type: list[list[float]]
    step_change = [[] for _ in range(steps)]  # type: list[list[float]]
    for points in group:
        game = points[0]["game_id"]
        targets = [_argmax(p) for p in points]
        changes = [float(a != b) for a, b in pairwise(targets)]
        drift_by_game[game].append(math.fsum(changes) / steps)
        once_by_game[game].append(float(any(changes)))
        branch_by_game[game].append(float(targets[0] != targets[-1]))
        for i, changed in enumerate(changes):
            step_change[i].append(changed)
        for i, (a, b) in enumerate(pairwise(points)):
            step_kl[i].append(metrics.kl_divergence_bits(b["conditional"], a["conditional"]))
            narrowed = _narrowed(a, b)
            if narrowed is not None:
                (informative if narrowed else filler).append(changes[i])
    for name, grouped in (
        ("drift_rate", drift_by_game),
        ("once_drift", once_by_game),
        ("branch_drift", branch_by_game),
    ):
        if len(grouped) >= MIN_CLUSTERS_FOR_BOOTSTRAP:
            getattr(report, name)[condition] = cluster_bootstrap(
                _sorted_clusters(grouped), lambda a: float(a.mean()), resamples, seed
            )
    report.step_kl[condition] = [math.fsum(v) / len(v) if v else math.nan for v in step_kl]
    report.step_change[condition] = [math.fsum(v) / len(v) if v else math.nan for v in step_change]
    if informative and filler:
        report.drift_by_information[condition] = (
            math.fsum(informative) / len(informative),
            len(informative),
            math.fsum(filler) / len(filler),
            len(filler),
        )


def render(reports: list[TurnReport]) -> str:
    """Render the turn-resolved outcomes as Markdown."""
    lines = [
        "# Experiment 1 — turn-resolved metrics (Tier 2)",
        "",
        "Luo et al.'s **Drift Rate** (`#changes / T`) and **KL** (`D_KL(P_t ‖ P_{t-1})`) as",
        "they define them, over the six-point trajectory `early → turn1 … turn4 → late`,",
        "with the positive control their design lacks: C1 and C2 place a target in the state,",
        "so drift has a measurable floor rather than an assumed one.",
        "",
        "`Branch D.R.` is their Appendix C metric, `1(p_T ≠ p_0)` — the quantity the two-point",
        "grid reports elsewhere in this package. It is shown beside the others so the",
        "difference between the proxy and the headline metric is visible rather than argued.",
        "",
        "**Tier 2. Tier 1 rests on state identity and does not depend on turn resolution.**",
        "",
    ]
    for report in reports:
        lines.append(f"## {report.model_key}")
        lines.append("")
        if not report.trajectories:
            lines.extend(f"> {note}" for note in report.notes)
            lines.append("")
            continue
        lines.append(f"Complete trajectories: {report.trajectories}")
        lines.append("")
        lines.append("| Condition | Drift Rate (#changes/T) | Once D.R. | Branch D.R. |")
        lines.append("|---|---|---|---|")
        lines.extend(
            f"| {c} | {_cell(report.drift_rate.get(c))} | {_cell(report.once_drift.get(c))} | "
            f"{_cell(report.branch_drift.get(c))} |"
            for c in sorted(report.drift_rate)
        )
        lines.append("")
        lines.append("Where the drift happens — fraction of trajectories changing target at")
        lines.append("each step, and the mean KL of that step in bits:")
        lines.append("")
        header = " | ".join(f"{a}→{b}" for a, b in pairwise(TRAJECTORY))
        lines.append(f"| Condition | | {header} |")
        lines.append("|---|---" + "|---" * (len(TRAJECTORY) - 1) + "|")
        for condition in sorted(report.step_change):
            changes = " | ".join(f"{v:.3f}" for v in report.step_change[condition])
            kls = " | ".join(f"{v:.2f}" for v in report.step_kl[condition])
            lines.append(f"| {condition} | changed | {changes} |")
            lines.append(f"| | KL (bits) | {kls} |")
        if report.distractor_mass:
            excluded, narrowing = report.distractor_excluded
            lines.append("**C4 — is the distractor retained, or merely available?** Mass on")
            lines.append("the previous game's index at each probe point, with the")
            lines.append("constraint-consistent answer beside it:")
            lines.append("")
            lines.append("| | " + " | ".join(TRAJECTORY) + " |")
            lines.append("|---" * (len(TRAJECTORY) + 1) + "|")
            lines.append(
                "| distractor | " + " | ".join(f"{v:.4f}" for v in report.distractor_mass) + " |"
            )
            lines.append(
                "| consistent | " + " | ".join(f"{v:.4f}" for v in report.consistent_mass_c4) + " |"
            )
            lines.append("")
            lines.append(
                f"A narrowing step excluded the distractor in {excluded} of {narrowing} cases: "
                "C4 places it outside the consistent set by construction, so a real constraint "
                "usually rules it out. Whether its mass then falls is what separates prior mass "
                "from a retained belief."
            )
            lines.append("")
        if report.drift_by_information:
            lines.append("**Does drift track turns, or information?** A filler question is")
            lines.append("universally true, so it adds a turn and narrows nothing. Under")
            lines.append('"the belief drifts over time" it should drift like any other step.')
            lines.append("")
            lines.append("| Condition | step narrowed the set | step narrowed nothing |")
            lines.append("|---|---|---|")
            lines.extend(
                f"| {c} | {inf:.3f} (n={n_inf}) | {fil:.3f} (n={n_fil}) |"
                for c, (inf, n_inf, fil, n_fil) in sorted(report.drift_by_information.items())
            )
            lines.append("")
        for note in report.notes:
            lines.append(f"> {note}")
            lines.append("")
    return "\n".join(lines)


def _cell(interval: Interval | None) -> str:
    if interval is None:
        return "—"
    return f"{interval.estimate:.3f} [{interval.low:.3f}, {interval.high:.3f}]"
