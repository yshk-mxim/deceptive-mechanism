# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Reproduce every Tier-1 number in the paper from the shipped JSONL.

    python -m deceit_analysis.cli --records data/records/tier1_records.jsonl

Needs only Python, numpy and scipy: no MLX, no model weights, no Apple hardware. That is
the reproducibility claim the replication package actually makes, and it is the one a
third party can check.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

from deceit_analysis import bare_value, selection, tier1, tier23, turn_resolved

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECORDS = PACKAGE_ROOT / "data" / "records" / "tier1_records.jsonl"
DEFAULT_TIERS23 = PACKAGE_ROOT / "data" / "records" / "tiers23_records.jsonl"
DEFAULT_BARE = PACKAGE_ROOT / "data" / "records" / "bare_value_records.jsonl"
DEFAULT_TURNS = PACKAGE_ROOT / "data" / "records" / "turn_resolved_records.jsonl"
#: Experiment 2 ships in its own package directory. It is a different experiment with a
#: different scenario; the only thing it shares with Experiment 1 is the harness and this
#: analysis package.
EXPERIMENT2_ROOT = PACKAGE_ROOT.parent / "experiment2"
DEFAULT_SELECTION = EXPERIMENT2_ROOT / "data" / "records" / "selection_records.jsonl"
DEFAULT_CONFIG = PACKAGE_ROOT / "configs" / "experiment1.toml"
DEFAULT_OUT = PACKAGE_ROOT / "results"


def load_thresholds(path: Path) -> dict[str, float]:
    """Read the pre-registered thresholds from the shipped config.

    Thresholds live in the config rather than in this module so that the numbers the
    analysis tests against are the same ones the pre-registration froze, and a reader can
    diff them without reading code.
    """
    with path.open("rb") as fh:
        return dict(tomllib.load(fh)["analysis"])


def main(argv: list[str] | None = None) -> int:
    """Run the Tier-1 analysis and write the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--tiers23", type=Path, default=DEFAULT_TIERS23)
    parser.add_argument("--bare", type=Path, default=DEFAULT_BARE)
    parser.add_argument("--turns", type=Path, default=DEFAULT_TURNS)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PACKAGE_ROOT / "data" / "manifests" / "stage01_tier1.json",
    )
    args = parser.parse_args(argv)

    if not tier1.records_available(args.records):
        print(f"records not found: {args.records}", file=sys.stderr)
        return 2

    thresholds = load_thresholds(args.config)
    with args.config.open("rb") as fh:
        samplers = {k: dict(v) for k, v in tomllib.load(fh)["models"].items()}
    records = tier1.load_records(args.records)
    try:
        fingerprint = tier1.assert_provenance_consistent(records, args.manifest)
    except ValueError as exc:
        print(f"PROVENANCE CHECK FAILED: {exc}", file=sys.stderr)
        return 3
    try:
        states = tier1.assert_state_identity(records)
    except ValueError as exc:
        print(f"STATE IDENTITY CHECK FAILED: {exc}", file=sys.stderr)
        return 4
    print(
        f"provenance: {len(records)} records, pipeline {fingerprint}\n"
        f"state identity: {states} states, each measured under one digest across its "
        f"readouts\n"
    )
    models = sorted({r["model_key"] for r in records})
    resamples = int(thresholds.get("bootstrap_resamples", 10000))
    reports = [
        tier1.analyse_model(records, model, thresholds, samplers, resamples, seed=0)
        for model in models
    ]

    path = tier1.write_report(reports, args.out)
    print(tier1.render_report(reports))
    print(f"\nwritten: {path}")

    for code in _optional_arms(args, records, thresholds, samplers, resamples):
        if code:
            return code

    failed = [g.name for r in reports for g in r.gates if not g.result.passed]
    failed += [c.name for r in reports for c in r.continuous_gates if not c.passed]
    if failed:
        print(f"\nGATES NOT PASSED: {', '.join(sorted(set(failed)))}")
    return 0


def run_tiers23(
    args: argparse.Namespace,
    records: list[dict[str, Any]],
    thresholds: dict[str, float],
    resamples: int,
) -> int:
    """Analyse the mechanism and Luo-replication arms, if their records are present.

    Tier 2 and Tier 3 are optional: Tier 1 stands on its own, and the package is useful
    before the mechanism and replication arms have run.

    Returns:
        A process exit code; 0 both on success and when the arm is simply absent.
    """
    if not tier1.records_available(args.tiers23):
        print(f"\n(no Tier-2/3 records at {args.tiers23}; Tier 1 reported alone)")
        return 0
    # Union with the Tier-1 records rather than analysing the Tier-2 file alone: C0 at
    # Regime D lives in the Tier-1 file while its matched C3 and C5 live here, and T9
    # compares them state-for-state. The union is legitimate only because both files carry
    # the same pipeline fingerprint, which is checked rather than assumed -- combining runs
    # from different source versions would silently compare different experiments.
    extra = records + tier1.load_records(args.tiers23)
    try:
        tier1.assert_provenance_consistent(extra, args.manifest)
        tier1.assert_state_identity(extra)
    except ValueError as exc:
        print(f"TIER-2/3 CHECK FAILED: {exc}", file=sys.stderr)
        return 3
    reports = [
        tier23.analyse(extra, model, thresholds, resamples, seed=0)
        for model in sorted({r["model_key"] for r in extra})
    ]
    rendered = tier23.render(reports)
    (args.out / "RESULTS_TIER23.md").write_text(rendered, encoding="utf-8")
    print()
    print(rendered)
    return 0


def _optional_arms(
    args: argparse.Namespace,
    records: list[dict[str, Any]],
    thresholds: dict[str, float],
    samplers: dict[str, dict[str, float]],
    resamples: int,
) -> list[int]:
    """Run every arm that is optional, in report order.

    Each returns 0 both on success and when its records are simply absent: Tier 1 stands on
    its own and the package is useful before the later arms have run.
    """
    return [
        run_tiers23(args, records, thresholds, resamples),
        run_bare_value(args, thresholds, resamples),
        run_turn_resolved(args, records, resamples),
        run_selection(args, thresholds, samplers, resamples),
    ]


def run_selection(
    args: argparse.Namespace,
    thresholds: dict[str, float],
    samplers: dict[str, dict[str, float]],
    resamples: int,
) -> int:
    """Analyse Experiment 2, if its records are present.

    Analysed on its own file: it is a different experiment with a different scenario, and
    the only thing it shares with Experiment 1 is the harness.

    Returns:
        A process exit code; 0 both on success and when the arm is simply absent.
    """
    if not tier1.records_available(args.selection):
        print(f"\n(no Experiment 2 records at {args.selection}; that experiment is UNRUN)")
        return 0
    records = tier1.load_records(args.selection)
    try:
        fingerprint = tier1.assert_provenance_consistent(
            records, EXPERIMENT2_ROOT / "data" / "manifests" / "stage05_selection.json"
        )
        states = tier1.assert_state_identity(records)
    except ValueError as exc:
        print(f"EXPERIMENT 2 CHECK FAILED: {exc}", file=sys.stderr)
        return 3
    print(f"\nexperiment 2: {len(records)} records, {states} states, pipeline {fingerprint}")
    reports = [
        selection.analyse(records, model, thresholds, samplers, resamples, seed=0)
        for model in sorted({r["model_key"] for r in records})
    ]
    rendered = selection.render(reports)
    out = EXPERIMENT2_ROOT / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "RESULTS.md").write_text(rendered, encoding="utf-8")
    print()
    print(rendered)
    return 0


def run_turn_resolved(
    args: argparse.Namespace, tier1_records: list[dict[str, Any]], resamples: int
) -> int:
    """Analyse the turn-resolved arm, if its records are present.

    Unioned with the Tier-1 records rather than analysed alone: the `early` and `late` end
    points of every trajectory live there and are not re-measured, so the six-point path is
    assembled by joining on (model, condition, game, readout). The union is legitimate only
    because both files carry the same pipeline fingerprint, which is checked.

    Returns:
        A process exit code; 0 both on success and when the arm is simply absent.
    """
    if not tier1.records_available(args.turns):
        print(f"\n(no turn-resolved records at {args.turns}; that arm is UNRUN)")
        return 0
    joined = tier1_records + tier1.load_records(args.turns)
    try:
        fingerprint = tier1.assert_provenance_consistent(
            joined, PACKAGE_ROOT / "data" / "manifests" / "stage04_turn_resolved.json"
        )
        tier1.assert_state_identity(joined)
    except ValueError as exc:
        print(f"TURN-RESOLVED CHECK FAILED: {exc}", file=sys.stderr)
        return 3
    print(f"\nturn-resolved: {len(joined)} records joined, pipeline {fingerprint}")
    reports = [
        turn_resolved.analyse(joined, model, resamples, seed=0)
        for model in sorted({r["model_key"] for r in joined})
    ]
    rendered = turn_resolved.render(reports)
    (args.out / "RESULTS_TURN_RESOLVED.md").write_text(rendered, encoding="utf-8")
    print()
    print(rendered)
    return 0


def run_bare_value(args: argparse.Namespace, thresholds: dict[str, float], resamples: int) -> int:
    """Analyse the bare-value arm, if its records are present.

    Analysed on its own file and never unioned with the index arm: the two measure
    different answer spaces at different states, so there is no state-matched comparison to
    make and a union would only invite one.

    Returns:
        A process exit code; 0 both on success and when the arm is simply absent.
    """
    if not tier1.records_available(args.bare):
        print(f"\n(no bare-value records at {args.bare}; that arm is UNRUN)")
        return 0
    records = tier1.load_records(args.bare)
    try:
        fingerprint = tier1.assert_provenance_consistent(
            records, PACKAGE_ROOT / "data" / "manifests" / "stage03_bare_value.json"
        )
        states = tier1.assert_state_identity(records)
    except ValueError as exc:
        print(f"BARE-VALUE CHECK FAILED: {exc}", file=sys.stderr)
        return 3
    print(f"\nbare-value: {len(records)} records, {states} states, pipeline {fingerprint}")
    reports = [
        bare_value.analyse(records, model, thresholds, resamples, seed=0)
        for model in sorted({r["model_key"] for r in records})
    ]
    rendered = bare_value.render(reports)
    (args.out / "RESULTS_BARE_VALUE.md").write_text(rendered, encoding="utf-8")
    print()
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
