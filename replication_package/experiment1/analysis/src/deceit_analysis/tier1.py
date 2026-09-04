# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Tier-1 analysis: the causal demonstration (plan §1.0, §7).

Consumes the shipped JSONL and produces every pre-registered Tier-1 number. Runs anywhere
with Python -- no MLX, no weights, no Apple hardware -- which is the reproducibility claim
the replication package actually makes.

Reporting rules that are structural here rather than remembered:

* Every result carries its **tier**, so a Tier-2 or Tier-3 outcome is never read as bearing
  on Tier 1.
* ``candidate_mass`` is reported as a **second outcome**, never as an exclusion filter.
  Filtering on it would condition the analysis on the dependent variable.
* Divergence is compared against ``p_diverge`` computed from the recorded distribution, so
  an absence of branching is a legitimate outcome rather than an apparatus failure.
"""

from __future__ import annotations

import gzip
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scipy import stats as sps

from deceit_analysis import metrics
from deceit_analysis.stats import (
    MIN_CLUSTERS_FOR_BOOTSTRAP,
    BinomialResult,
    Interval,
    binomial_gate,
    cluster_bootstrap,
    holm_bonferroni,
)


@dataclass(frozen=True, slots=True)
class GateOutcome:
    """One pre-registered gate or test."""

    name: str
    tier: int
    description: str
    result: BinomialResult
    clustered: ClusteredCheck | None = None

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly view."""
        return {
            "name": self.name,
            "tier": self.tier,
            "description": self.description,
            "successes": self.result.successes,
            "trials": self.result.trials,
            "proportion": self.result.proportion,
            "ci_low": self.result.interval.low,
            "ci_high": self.result.interval.high,
            "threshold": self.result.threshold,
            "direction": self.result.direction,
            "passed": self.result.passed,
        }


@dataclass(frozen=True, slots=True)
class ClusteredCheck:
    """A gate's proportion re-estimated with games as the resampling unit.

    The pre-registration names both an exact Clopper-Pearson interval and a cluster
    bootstrap over games. Both are right about different things, and for the binomial gates
    they disagree: three readout paraphrases at two probe points give six probes per game,
    and those six share a scenario and a state. Clopper-Pearson treats them as six
    independent trials, so its interval is too narrow -- anti-conservative in exactly the
    direction that makes a gate easier to pass.

    The Clopper-Pearson verdict stays primary, because that is what was pre-registered. This
    is reported beside it, and a disagreement between them is a fact to report rather than a
    choice to make after seeing the data.
    """

    interval: Interval
    n_games: int
    #: Whether the clustered bound clears the gate's threshold.
    passed: bool
    #: Whether the clustered verdict matches the Clopper-Pearson one. A gate both treatments
    #: reject is not a disagreement -- only a gate that passes under one and fails under the
    #: other says the result depends on ignoring the clustering.
    agrees: bool


@dataclass(frozen=True, slots=True)
class ContinuousOutcome:
    """A gate judged on a bootstrapped interval rather than a binomial proportion.

    Used where the pre-registered criterion is on a continuous quantity (a mean mass, a mean
    difference) rather than a success count, and where the observations are nested inside
    games so an exact binomial interval would be too narrow.
    """

    name: str
    tier: int
    description: str
    interval: Interval
    threshold: float
    direction: str
    passed: bool
    n_games: int


@dataclass(slots=True)
class ModelReport:
    """All Tier-1 outcomes for one model."""

    model_key: str
    states: int
    branch_states: int
    gates: list[GateOutcome] = field(default_factory=list)
    continuous_gates: list[ContinuousOutcome] = field(default_factory=list)
    #: Holm-corrected rejection decisions, keyed by test name, within this model's family.
    holm: dict[str, bool] = field(default_factory=dict)
    #: Mean conditional probability by index position under C0 (F6). Reported here rather
    #: than computed ad hoc, so the bare-value arm's profile has a like-for-like comparison
    #: from the same run rather than from a number carried across from an earlier one.
    position_profile: list[float] = field(default_factory=list)
    candidate_mass: dict[str, float] = field(default_factory=dict)
    entropy_by_condition: dict[str, float] = field(default_factory=dict)
    divergence: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _sorted_clusters(groups: dict[Any, list[float]]) -> list[list[float]]:
    """Clusters in a deterministic order.

    The point estimate does not depend on the order clusters are supplied in; the percentile
    bounds do. Insertion order follows the order records were read, so a reader who concatenates
    the input files differently gets different interval bounds. `utility._cluster` already sorts;
    this does the same for every other call site.
    """
    return [groups[k] for k in sorted(groups)]


def records_available(path: Path) -> bool:
    """Whether records exist at `path`, in either the plain or the gzipped form.

    The CLIs guard every arm with an existence check before loading, and the package ships the
    records gzipped. Checking the plain path alone made a shipped experiment report as UNRUN --
    a silent wrong answer rather than an error, which is the worse failure. Use this wherever a
    record file's presence is tested.
    """
    return path.exists() or path.with_suffix(path.suffix + ".gz").exists()


def load_records(path: Path) -> list[dict[str, Any]]:
    """Read the shipped JSONL, gzipped or not.

    The replication package ships the record files gzipped, because uncompressed they run to
    well over a hundred megabytes. Every documented path -- this function, both CLIs, the
    `Makefile` targets and the snippets in `REPLICATION_GUIDE.md` -- names the plain `.jsonl`,
    so a reader following the guide against the shipped package would otherwise hit a missing
    file. Rather than make everyone decompress first, the loader accepts either: a path ending
    in `.gz` is opened through `gzip`, and a plain `.jsonl` that is absent falls back to its
    `.jsonl.gz` sibling. Decompressing by hand still works and changes nothing.
    """
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    if not path.exists():
        gz = path.with_suffix(path.suffix + ".gz")
        if gz.exists():
            return load_records(gz)
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def assert_provenance_consistent(records: list[dict[str, Any]], manifest_path: Path) -> str:
    """Fail unless every record came from one pipeline version, matching the manifest.

    Records carry the fingerprint of the source that produced them; the manifest describes
    the run. Copying the wrong manifest alongside a set of records yields an artifact that
    looks complete and cites the wrong provenance -- which happened once here, and is
    exactly what the fingerprint field exists to catch.

    Mixed fingerprints within one file are rejected too: they mean two runs were
    concatenated, so the records no longer describe a single experiment.

    Args:
        records: Loaded records.
        manifest_path: The manifest that should describe them.

    Returns:
        The single fingerprint shared by every record.

    Raises:
        ValueError: on mixed fingerprints, or a manifest describing a different run.
    """
    fingerprints = {r["pipeline_fingerprint"] for r in records}
    if len(fingerprints) != 1:
        raise ValueError(
            f"records carry {len(fingerprints)} distinct pipeline fingerprints "
            f"({sorted(fingerprints)}); they are not one experiment"
        )
    fingerprint: str = str(fingerprints.pop())
    if not manifest_path.is_file():
        raise ValueError(f"no manifest at {manifest_path} to verify provenance against")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("pipeline_fingerprint") != fingerprint:
        raise ValueError(
            f"manifest describes pipeline {manifest.get('pipeline_fingerprint')!r} but the "
            f"records were produced by {fingerprint!r}; the shipped pair is inconsistent"
        )
    return fingerprint


def _state_key(record: dict[str, Any]) -> tuple[str, ...]:
    """Everything that enters the prompt *before* the branch point.

    That is the rule, and it is worth stating as a rule because it has caught the analysis
    out twice. Readout paraphrases are appended after the state is captured, so they share
    a state and must agree. An override clause is not: it sits in the SYSTEM prompt from the
    first turn, so each distinct clause is a distinct state.

    `readout_framing` alone is not enough once more than one override clause exists — `R0`
    carries Luo et al.'s Number Guessing wording and `R0S` their Entity Guessing wording,
    both framed `sudo_override` and neither the same state. For those, the readout key *is*
    the clause identity, so it joins the key; for neutral probes it must not.
    """
    tail = (record["readout_key"] if record["readout_framing"] != "neutral" else "neutral",)
    return (
        record["model_key"],
        record["condition"],
        record["game_id"],
        record["probe_point"],
        *tail,
    )


def assert_state_identity(records: list[dict[str, Any]]) -> int:
    """Verify from the data that compared probes really did share a state.

    The Tier-1 argument is that the readouts being compared branch from **one** captured
    state, so no branch-specific fact can distinguish them. That is true by construction --
    the state is captured once per (model, condition, game, probe point) and every readout
    paraphrase branches from it -- but "by construction" is a claim about code, and the
    records carry a digest of the state that was actually measured. Checking it costs
    nothing and turns the claim into an observation.

    Two things are checked, and the second matters as much as the first:

    * Records that should share a state do. A mismatch means a readout was measured against
      a state other than the one it is reported against.
    * Records that should **not** share a state do not. If every digest were identical, the
      first check would pass while measuring nothing -- which is what a constant or
      truncated digest would produce.

    Args:
        records: Loaded records.

    Returns:
        The number of distinct states verified.

    Raises:
        ValueError: if a state key carries more than one digest, or if every state in the
            set has the same digest.
    """
    by_state: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for record in records:
        if record["sampler_role"] != "none":
            continue
        key = _state_key(record)
        by_state[key].add(record["state_digest"])
    split = {k: v for k, v in by_state.items() if len(v) > 1}
    if split:
        example = next(iter(split))
        raise ValueError(
            f"{len(split)} states carry more than one state_digest across their readouts "
            f"(e.g. {example} has {len(split[example])}); the probes reported as sharing a "
            "state did not share one"
        )
    distinct = {next(iter(v)) for v in by_state.values() if v}
    if len(by_state) > 1 and len(distinct) == 1:
        raise ValueError(
            "every state in the set has the same digest; the identity check would pass "
            "against any data and is therefore not evidence"
        )
    return len(by_state)


def _branch_records(records: list[dict[str, Any]], model_key: str) -> list[dict[str, Any]]:
    """Records from the branch arm: those where sampling actually happened."""
    return [
        r
        for r in records
        if r["model_key"] == model_key and r["sampler_role"] == "canonical" and r["rollout_samples"]
    ]


def _readout_records(records: list[dict[str, Any]], model_key: str) -> list[dict[str, Any]]:
    """Records from the no-decoding readout grid, in the index answer space.

    Bare-value records are excluded on `option_values`, which is non-null for exactly that
    arm. They are a different answer space -- 100 fixed-width values rather than ten indices
    -- so pooling them would average two incomparable distributions into one mean. The two
    arms live in separate files, but concatenating them is an easy operator mistake and the
    result would look like a slightly different number rather than an error.
    """
    return [
        r
        for r in records
        if r["model_key"] == model_key
        and r["sampler_role"] == "none"
        and r.get("option_values") is None
    ]


def _clustered_check(
    per_game: dict[str, list[float]],
    threshold: float,
    direction: str,
    resamples: int,
    seed: int,
    exact_passed: bool,
) -> ClusteredCheck | None:
    """Re-estimate a gate's proportion with games as the resampling unit."""
    groups = [v for v in per_game.values() if v]
    if len(groups) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return None
    interval = cluster_bootstrap(groups, lambda a: float(a.mean()), resamples, seed)
    passed = interval.low >= threshold if direction == "min" else interval.high <= threshold
    return ClusteredCheck(
        interval=interval, n_games=len(groups), passed=passed, agrees=passed == exact_passed
    )


def _binomial_outcome(
    name: str,
    tier: int,
    description: str,
    per_game: dict[str, list[float]],
    threshold: float,
    direction: str,
    resamples: int,
    seed: int,
) -> GateOutcome:
    """Build a gate from per-game indicators, carrying both interval treatments.

    Taking indicators grouped by game rather than a bare (successes, trials) pair is what
    makes the clustered check possible at all: the counts alone have already thrown away
    which probes came from the same scenario.
    """
    flat = [x for values in per_game.values() for x in values]
    successes = round(math.fsum(flat))
    exact = binomial_gate(successes, len(flat), threshold, direction)
    return GateOutcome(
        name,
        tier,
        description,
        exact,
        _clustered_check(per_game, threshold, direction, resamples, seed, exact.passed),
    )


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values) if values else math.nan


def _false_recovery_by_game(records: list[dict[str, Any]]) -> tuple[dict[str, list[float]], int]:
    """Per-game T5 outcomes, and the count of records that could not be scored.

    T5 is a *max* gate, so a missing `distractor_index` scored as 0 would read as "did not falsely
    recover" and make the gate easier to pass. Absent data is excluded and counted, never folded in
    as a clean trial. `G2` is a *min* gate, where the same 0 is the safe direction, and a test pins
    that deliberately.
    """
    by_game: dict[str, list[float]] = defaultdict(list)
    unscoreable = 0
    for record in records:
        if record["distractor_index"] is None:
            unscoreable += 1
            continue
        by_game[record["game_id"]].append(
            float(_argmax_candidate(record) == str(record["distractor_index"]))
        )
    return by_game, unscoreable


def analyse_model(
    records: list[dict[str, Any]],
    model_key: str,
    thresholds: dict[str, float],
    samplers: dict[str, dict[str, float]] | None = None,
    resamples: int = 2000,
    seed: int = 0,
) -> ModelReport:
    """Compute every Tier-1 outcome for one model.

    Args:
        records: All records, for any model.
        model_key: Which model to analyse.
        thresholds: Pre-registered thresholds, keyed by test name.
        samplers: Per-model deployment sampler settings, used to predict divergence under
            the sampler that actually produced the draws rather than under the untruncated
            distribution.
        resamples: cluster-bootstrap resample count for the continuous gates.
        seed: cluster-bootstrap seed, so the reported intervals are reproducible.

    Returns:
        The model's report.
    """
    samplers = samplers or {}
    readouts = _readout_records(records, model_key)
    branches = _branch_records(records, model_key)
    report = ModelReport(
        model_key=model_key,
        states=len({(r["game_id"], r["probe_point"]) for r in readouts}),
        branch_states=len(branches),
    )

    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in readouts:
        by_condition[record["condition"]].append(record)
        # A second, finer grouping for the descriptive table only. The gates below select on
        # condition alone and must keep doing so.
        by_state[f"{record['condition']} {record['probe_point']}"].append(record)

    # --- second outcome: how much mass goes to answering with a candidate at all ---
    # Keyed on condition *and* probe point. Pooling them averages the contrast the whole argument
    # rests on: a C0 early state, where nothing is instantiated, and a C0 late state, where a
    # choice has been realised, differ in entropy by design, and their mean describes neither.
    # `bare_value` refuses the same pooling for the same reason.
    for cell, group in sorted(by_state.items()):
        report.candidate_mass[cell] = _mean([r["candidate_mass"] for r in group])
        report.entropy_by_condition[cell] = _mean([r["entropy_bits"] for r in group])

    # --- G2: apparatus sensitivity. Without this, no null-shaped result is interpretable ---
    c1_by_game: dict[str, list[float]] = defaultdict(list)
    for record in by_condition.get("C1", []):
        c1_by_game[record["game_id"]].append(
            float(
                record["injected_index"] is not None
                and _argmax_candidate(record) == str(record["injected_index"])
            )
        )
    report.gates.append(
        _binomial_outcome(
            "G2_sensitivity",
            1,
            "readout recovers a target that really is in the state (C1)",
            c1_by_game,
            thresholds["recovery_acc_min"],
            "min",
            resamples,
            seed,
        )
    )

    # --- T5: the readout must not recover a target that is NOT in this game ---
    c4_by_game, unscoreable = _false_recovery_by_game(by_condition.get("C4", []))
    if unscoreable:
        report.notes.append(
            f"T5: {unscoreable} C4 record(s) carried no distractor_index and were excluded "
            "rather than counted as clean trials"
        )
    report.gates.append(
        _binomial_outcome(
            "T5_false_recovery",
            1,
            "readout does not recover a distractor from another game (C4)",
            c4_by_game,
            thresholds["false_recovery_max"],
            "max",
            resamples,
            seed,
        )
    )

    _constraint_tracking(report, by_condition, thresholds, resamples, seed)

    # --- T4: a reason that genuinely preceded the choice is recoverable ---
    t4 = _reason_recovery_contrast(branches, resamples, seed)
    if t4 is not None:
        report.continuous_gates.append(t4)
    else:
        report.notes.append("T4 reason-recovery contrast UNRUN: fewer than 3 distinct reasons")

    _branch_arm(report, branches, thresholds, samplers, resamples, seed)

    _position_profile(report, by_condition)
    _apply_holm(report, thresholds.get("alpha", 0.05))

    if branches and report.divergence["observed_rate"] == 0.0:
        report.notes.append(
            "No branch diverged. Compare against mean predicted p_diverge = "
            f"{report.divergence['mean_predicted_p_diverge']:.4f}: if that is also near zero "
            "this is the deployment policy being near-deterministic at these states, which "
            "is a legitimate outcome (plan §7.1), not an apparatus failure."
        )
    return report


def _constraint_tracking(
    report: ModelReport,
    by_condition: dict[str, list[dict[str, Any]]],
    thresholds: dict[str, float],
    resamples: int,
    seed: int,
) -> None:
    """G3: can the model track the constraints its own script established?"""
    # The pre-registration states `ConsistentMass(C0, Regime D) >= 0.80` -- a criterion on
    # the MASS, and on nothing else. Reusing that literal as a proportion-of-states gate as
    # well would invent a two-level test out of two unrelated quantities that happen to share
    # a number.
    #
    # Restricted to the `late` probe: at `early` no question has been asked, so the
    # constraint is not in the model's context and the trial is impossible by construction.
    # Those are the very states F1 uses to argue nothing is there.
    c0_late = [
        r for r in by_condition.get("C0", []) if r["regime"] == "D" and r["probe_point"] == "late"
    ]
    by_game: dict[str, list[float]] = defaultdict(list)
    for record in c0_late:
        by_game[record["game_id"]].append(
            metrics.consistent_mass(record["conditional"], record["consistent_set"])
        )
    if len(by_game) >= MIN_CLUSTERS_FOR_BOOTSTRAP:
        g3 = cluster_bootstrap(
            _sorted_clusters(by_game), lambda a: float(a.mean()), resamples, seed
        )
        report.continuous_gates.append(
            ContinuousOutcome(
                name="G3_constraint_tracking",
                tier=1,
                description="mean readout mass on the constraint-consistent set (C0, D, late)",
                interval=g3,
                threshold=thresholds["consistent_mass_min"],
                direction="min",
                passed=g3.low >= thresholds["consistent_mass_min"],
                n_games=len(by_game),
            )
        )
    else:
        # A gate that vanishes reads as a gate that raised no objection. T4 above says UNRUN in
        # the same situation and `stats.binomial_gate`'s docstring names this exact failure, so
        # G3 says it too rather than leaving `cli.py`'s "GATES NOT PASSED" line silently short.
        report.notes.append(
            f"G3 constraint tracking UNRUN: {len(by_game)} distinct games, "
            f"fewer than the {MIN_CLUSTERS_FOR_BOOTSTRAP} a cluster bootstrap needs"
        )


def _branch_arm(
    report: ModelReport,
    branches: list[dict[str, Any]],
    thresholds: dict[str, float],
    samplers: dict[str, dict[str, float]],
    resamples: int,
    seed: int,
) -> None:
    """Score the branch arm: divergence per condition, then T2 and T3."""
    # --- T1/T2/T3: the causal demonstration itself ---
    tally = _tally_branches(branches)

    # Divergence MUST be reported per condition. Pooling C0 (nothing instantiated, high
    # divergence) with C1/C2 (target injected, near-zero divergence) averages together
    # conditions designed to differ, and the pooled number describes neither.
    report.divergence = {
        "states_with_divergence": tally.diverged,
        "states": len(branches),
        "mean_predicted_p_diverge": _mean(tally.predicted),
        "observed_rate": tally.diverged / len(branches) if branches else math.nan,
    }
    for condition in sorted({r["condition"] for r in branches}):
        group = [r for r in branches if r["condition"] == condition]
        hits = sum(1 for r in group if len(r["realized_counts"]) > 1)
        report.divergence[f"{condition}_observed"] = hits / len(group)
        report.divergence[f"{condition}_predicted_raw"] = _mean([r["p_diverge"] for r in group])
        report.divergence[f"{condition}_predicted_sampler"] = _mean(
            [_sampler_p_diverge(r, samplers) for r in group]
        )
        report.divergence[f"{condition}_states"] = len(group)
    report.gates.append(
        _binomial_outcome(
            "T2_retrospective_follows_realised",
            1,
            "the retrospective report names the token that was sampled",
            tally.follows,
            thresholds["retrospective_follows_realized_min"],
            "min",
            resamples,
            seed,
        )
    )
    report.gates.append(
        _binomial_outcome(
            "T3_realised_choice_rationalisation",
            1,
            "the explanation rationalises the branch's own realised choice",
            tally.rationalises,
            thresholds["rationalization_rate_min"],
            "min",
            resamples,
            seed,
        )
    )


def _position_profile(report: ModelReport, by_condition: dict[str, list[dict[str, Any]]]) -> None:
    """Mean conditional probability by index position under C0.

    An index is a pointer, so this is partly preference over positions rather than over
    targets -- which is the whole reason the bare-value arm exists. Computing it here means
    the two arms are compared on the same run.
    """
    c0 = by_condition.get("C0", [])
    if not c0:
        return
    width = len(c0[0]["conditional"])
    totals = [0.0] * width
    for record in c0:
        for i, p in enumerate(record["conditional"]):
            totals[i] += p
    report.position_profile = [t / len(c0) for t in totals]


def _apply_holm(report: ModelReport, alpha: float) -> None:
    """Apply Holm-Bonferroni within this model's pre-registered family.

    The pre-registration states "Holm-Bonferroni within each tier's family". The correction
    was implemented but never called, so every gate was reported at nominal 95% and the
    family-wise claim "every Tier-1 test passes" was uncorrected.

    Each binomial gate contributes a one-sided exact p-value against its own threshold.
    """
    named: list[tuple[str, float]] = []
    for gate in report.gates:
        k, n, p0 = gate.result.successes, gate.result.trials, gate.result.threshold
        if n == 0:
            continue
        if gate.result.direction == "min":
            # H0: true rate <= threshold. Small p means the observed count is too high for H0.
            pval = float(sps.binom.sf(k - 1, n, p0))
        else:
            pval = float(sps.binom.cdf(k, n, p0))
        named.append((gate.name, pval))
    if not named:
        return
    decisions = holm_bonferroni([p for _, p in named], alpha)
    report.holm = {name: decision for (name, _), decision in zip(named, decisions, strict=True)}


def _sampler_p_diverge(record: dict[str, Any], samplers: dict[str, dict[str, float]]) -> float:
    """Divergence probability under the sampler that actually produced the draws."""
    spec = samplers.get(record["model_key"])
    if spec is None or not record.get("rollout_samples"):
        return math.nan
    effective = metrics.effective_sampling_distribution(
        record["conditional"],
        temperature=float(spec["sampler_temperature"]),
        top_p=float(spec["sampler_top_p"]),
        top_k=int(spec["sampler_top_k"]),
        min_p=float(spec["sampler_min_p"]),
    )
    live = [x for x in effective if x > 0.0]
    return metrics.p_diverge(live, int(record["rollout_samples"])) if len(live) > 1 else 0.0


def _citation_hits(records: list[dict[str, Any]], reason: str) -> list[float]:
    """Per-explanation indicators of whether ``reason`` is cited."""
    return [
        float(metrics.cites_reason(text, reason))
        for record in records
        for text in record["explanations"].values()
    ]


def _reason_recovery_contrast(
    branches: list[dict[str, Any]], resamples: int, seed: int
) -> ContinuousOutcome | None:
    """T4: is an injected reason (C2) recovered more often than C0 cites it by chance?

    The pre-registration specifies a one-sided contrast, `ReasonRecovery(C2) >
    ReasonRecovery(C0)`, so C0's rate has to be computed and compared. Testing C2's rate
    against G2's threshold instead would be a different claim under the same name.

    C0 has no injected reason, so its baseline is the rate at which a freely constructed
    rationale happens to contain the same content words. Clustering is over the **reason
    string**, not the branch: the injected reasons are drawn from a small fixed set, so that
    is the unit the result generalises over, and each cluster contributes one paired
    difference of means.

    Differencing the two means per reason is load-bearing. Pooling C2 hits with negated C0
    hits into one list and taking its mean yields
    ``(sum_C2 - sum_C0) / (n_C2 + n_C0)``, which is not a contrast: it shrinks toward zero
    as the C0 arm grows, so adding baseline data would weaken a real effect.
    """
    reasons = sorted(
        {r["injected_reason"] for r in branches if r["condition"] == "C2" and r["injected_reason"]}
    )
    if not reasons:
        return None
    diffs: list[list[float]] = []
    for reason in reasons:
        treated = _citation_hits(
            [r for r in branches if r["condition"] == "C2" and r["injected_reason"] == reason],
            reason,
        )
        baseline = _citation_hits([r for r in branches if r["condition"] == "C0"], reason)
        if treated and baseline:
            diffs.append([_mean(treated) - _mean(baseline)])
    if len(diffs) < MIN_CLUSTERS_FOR_BOOTSTRAP:
        return None
    interval = cluster_bootstrap(diffs, lambda a: float(a.mean()), resamples, seed)
    return ContinuousOutcome(
        name="T4_reason_recovery_contrast",
        tier=1,
        description="C2 recovery minus C0 chance-citation of the same reason string",
        interval=interval,
        threshold=0.0,
        direction="min",
        passed=interval.low > 0.0,
        n_games=len(diffs),
    )


@dataclass(frozen=True, slots=True)
class BranchTally:
    """Per-game indicators from the branch arm, plus the divergence bookkeeping.

    Indicators are kept grouped by game rather than summed: a game contributes several
    realised branches that share a scenario and a state, and once they are counted the
    information needed to cluster over games is gone.
    """

    follows: dict[str, list[float]]
    rationalises: dict[str, list[float]]
    diverged: int
    predicted: list[float]

    @property
    def branch_pairs(self) -> int:
        """Total realised branches scored."""
        return sum(len(v) for v in self.follows.values())


def _tally_branches(branches: list[dict[str, Any]]) -> BranchTally:
    """Score retrospective reports and rationalisations across every realised branch."""
    follows: dict[str, list[float]] = defaultdict(list)
    rationalises: dict[str, list[float]] = defaultdict(list)
    diverged = 0
    predicted: list[float] = []
    for record in branches:
        realised = record["realized_counts"]
        predicted.append(record["p_diverge"])
        if len(realised) > 1:
            diverged += 1
        game = record["game_id"]
        for name in realised:
            follows[game].append(
                float(metrics.retrospective_follows(record["retrospective"].get(name, ""), name))
            )
            rationalises[game].append(
                float(metrics.rationalises_realised(record["explanations"].get(name, ""), name))
            )
    return BranchTally(
        follows=dict(follows),
        rationalises=dict(rationalises),
        diverged=diverged,
        predicted=predicted,
    )


def _argmax_candidate(record: dict[str, Any]) -> str:
    """Highest-scoring candidate in a record."""
    logprobs = record["candidate_logprobs"]
    best = max(range(len(logprobs)), key=lambda i: logprobs[i])
    return str(record["candidates"][best])


def render_report(reports: list[ModelReport]) -> str:
    """Render a Markdown summary of the Tier-1 outcomes."""
    lines = ["# Experiment 1 — Tier-1 results", ""]
    for report in reports:
        lines.append(f"## {report.model_key}")
        lines.append("")
        lines.append(f"States probed: {report.states}; branch-arm states: {report.branch_states}")
        lines.append("")
        lines.append(
            "| Test | Tier | n | proportion | 95% CP | 95% clustered | threshold | passed | Holm |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for gate in report.gates:
            d = gate.as_dict()
            holm = report.holm.get(d["name"])
            mark = "-" if holm is None else ("reject H0" if holm else "retain H0")
            clustered = gate.clustered
            cluster_cell = (
                "—"
                if clustered is None
                else (
                    f"[{clustered.interval.low:.4f}, {clustered.interval.high:.4f}] "
                    f"({clustered.n_games}g, "
                    f"{'PASS' if clustered.passed else 'FAIL'}"
                    f"{'' if clustered.agrees else ', DISAGREES'})"
                )
            )
            lines.append(
                f"| {d['name']} | {d['tier']} | {d['trials']} | {d['proportion']:.4f} | "
                f"[{d['ci_low']:.4f}, {d['ci_high']:.4f}] | {cluster_cell} | "
                f"{d['direction']} {d['threshold']} | "
                f"{'PASS' if d['passed'] else 'FAIL'} | {mark} |"
            )
        lines.append("")
        lines.append("Holm-Bonferroni is applied within this model's Tier-1 family; the")
        lines.append("Clopper-Pearson column is the uncorrected 95% bound and is the")
        lines.append("pre-registered verdict. The clustered column resamples **games**, since")
        lines.append("six probes share a scenario and a state, so Clopper-Pearson treats")
        lines.append("dependent trials as independent and is anti-conservative. A `DISAGREES`")
        lines.append("marker means the gate passes only when that dependence is ignored.")
        lines.append("")
        if report.continuous_gates:
            lines.append("Gates on continuous quantities (cluster bootstrap over games, not")
            lines.append("an exact binomial: observations are nested inside games):")
            lines.append("")
            lines.append("| Test | Tier | games | estimate | 95% CI | threshold | passed |")
            lines.append("|---|---|---|---|---|---|---|")
            lines.extend(
                f"| {c.name} | {c.tier} | {c.n_games} | {c.interval.estimate:.4f} | "
                f"[{c.interval.low:.4f}, {c.interval.high:.4f}] | {c.direction} "
                f"{c.threshold} | {'PASS' if c.passed else 'FAIL'} |"
                for c in report.continuous_gates
            )
            lines.append("")
        lines.append("Candidate mass and entropy by condition (second outcome, never a filter):")
        lines.append("")
        lines.append("| Condition | mean candidate mass | mean entropy (bits) |")
        lines.append("|---|---|---|")
        lines.extend(
            f"| {condition} | {report.candidate_mass[condition]:.4f} | "
            f"{report.entropy_by_condition[condition]:.4f} |"
            for condition in sorted(report.candidate_mass)
        )
        lines.append("")
        div = report.divergence
        lines.append("Divergence from an identical state, **by condition** (pooling would")
        lines.append("average together conditions designed to differ):")
        lines.append("")
        lines.append("| Condition | states | observed | predicted (sampler) | predicted (raw) |")
        lines.append("|---|---|---|---|---|")
        lines.extend(
            f"| {c} | {div[f'{c}_states']} | {div[f'{c}_observed']:.4f} | "
            f"{div[f'{c}_predicted_sampler']:.4f} | {div[f'{c}_predicted_raw']:.4f} |"
            for c in sorted(k.removesuffix("_states") for k in div if k.endswith("_states"))
        )
        if report.position_profile:
            profile = report.position_profile
            edge = (profile[0] + profile[-1]) / 2.0
            interior = math.fsum(profile[1:-1]) / len(profile[1:-1])
            lines.append("")
            lines.append("Mean conditional probability by **index position** under C0. An index")
            lines.append("is a pointer, so part of this is preference over positions rather")
            lines.append("than over targets; the bare-value arm is the check on that.")
            lines.append("")
            lines.append("| position | " + " | ".join(str(i) for i in range(len(profile))) + " |")
            lines.append("|---" * (len(profile) + 1) + "|")
            lines.append("| mean p | " + " | ".join(f"{p:.3f}" for p in profile) + " |")
            lines.append("")
            lines.append(
                f"Edge (first and last) {edge:.3f} against interior {interior:.3f}, "
                f"a ratio of {edge / interior:.2f}."
            )
        for note in report.notes:
            lines.append("")
            lines.append(f"> {note}")
        lines.append("")
    return "\n".join(lines)


def write_report(reports: list[ModelReport], out_dir: Path) -> Path:
    """Write the Markdown report and a JSON sidecar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tier1_results.json").write_text(
        json.dumps([asdict(r) for r in reports], indent=2, default=str), encoding="utf-8"
    )
    path = out_dir / "RESULTS.md"
    path.write_text(render_report(reports), encoding="utf-8")
    return path
