# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""Reproduce every pinned Experiment 3/4/5 number from the shipped JSONL.

    python -m deceit_analysis.cli_345

Experiments 1 and 2 have `cli.py`: a committed entry point that reads `bootstrap_resamples`
from the shared config and fixes `seed=0`, so their confidence intervals reproduce bit-for-bit.
Experiments 3, 4 and 5 have no such entry point (`REPLICATION_GUIDE.md`, "Which analysis
function regenerates which experiment's numbers": `utility.analyse`, `provenance.analyse` and
`recipient.analyse` are exercised only from each module's own test file), so nothing in the
repository records the resamples and seed that produced a published interval.

This is a **sibling module, not an extension of `cli.py`**. `cli.py`'s structure -- manifests
plus `data/records/`, a `thresholds` dict threaded through `tier1.analyse_model`, optional arms
unioned onto one Tier-1 file -- is specific to Experiment 1's layout and does not fit
Experiments 3-5: their data lives flat in `data/` (`REPLICATION_GUIDE.md`, "Layout note"), each
experiment is its own file (or small family of files, for E4's re-scoring passes), and
`utility`/`provenance`/`recipient` take a single `check_threshold` rather than a thresholds
dict. Reusing `cli.py`'s shape here would force those differences to disappear rather than
recording them.

**The parameters are pinned to what the guide documents.** `bootstrap_resamples` still comes
from `configs/experiment1.toml` -- the one shared config, so there remains one source of truth
for the resample count -- and the seed is fixed at 0, exactly as `cli.py` fixes it. Both match
the exact invocation the guide gives, and `check_threshold=0.9` matches its statement that this
is "the value used at every call site checked" (`PREREGISTRATION_U2_RERUN.md` and every
`test_utility.py`/`test_provenance.py`/`test_recipient.py` call site agree). Running this module
twice gives byte-identical intervals and p-values; no other value ever attaches to a run.

Needs only Python, numpy and scipy: no MLX, no model weights, no Apple hardware -- the same
reproducibility claim `cli.py` makes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deceit_analysis import provenance, recipient, tier1, utility
from deceit_analysis.cli import load_thresholds
from deceit_analysis.stats import BinomialResult, Interval
from deceit_analysis.utility import Contrast

#: Experiment 1's own directory -- `cli.py`'s `PACKAGE_ROOT`, four levels up from this file.
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
#: The replication package root: Experiments 3-5 are siblings of Experiment 1, not children of
#: it, exactly as `cli.py` treats Experiment 2 (`EXPERIMENT2_ROOT`).
REPL_ROOT = PACKAGE_ROOT.parent
EXPERIMENT3_ROOT = REPL_ROOT / "experiment3"
EXPERIMENT4_ROOT = REPL_ROOT / "experiment4"
EXPERIMENT5_ROOT = REPL_ROOT / "experiment5"

DEFAULT_UTILITY = EXPERIMENT3_ROOT / "data" / "utility_records.jsonl"
DEFAULT_UTILITY_RERUN = EXPERIMENT3_ROOT / "data" / "utility_rerun_records.jsonl"
DEFAULT_PROVENANCE = EXPERIMENT4_ROOT / "data" / "provenance_records.jsonl"
DEFAULT_RERENDERED = EXPERIMENT4_ROOT / "data" / "rerendered_records.jsonl"
DEFAULT_TRUNCATED = EXPERIMENT4_ROOT / "data" / "truncated_records.jsonl"
DEFAULT_RECIPIENT = EXPERIMENT5_ROOT / "data" / "recipient_records.jsonl"
#: The one shared config `bootstrap_resamples` is read from -- Experiment 1's, since it is the
#: only config this package ships and `cli.py` already treats it as the single source of truth
#: for the resample count.
DEFAULT_CONFIG = PACKAGE_ROOT / "configs" / "experiment1.toml"

#: Accuracy a manipulation/representation check must reach to count as represented.
#: `REPLICATION_GUIDE.md`: "always with check_threshold=0.9 in every call site checked".
CHECK_THRESHOLD = 0.9

#: The cluster-bootstrap RNG seed. Fixed for the same reason `cli.py` fixes Experiment 1 and
#: 2's at 0: an entry point commits to one number rather than leaving every recomputation to
#: draw its own, and reusing `cli.py`'s own value keeps one convention across the package.
SEED = 0


def _fmt_interval(interval: Interval) -> str:
    """Format a point estimate and its bootstrap interval to four decimal places."""
    return f"{interval.estimate:+.4f} [{interval.low:+.4f}, {interval.high:+.4f}]"


def _fmt_contrast(contrast: Contrast) -> str:
    """Format one named contrast: its interval, bootstrap p-value, direction and arm sizes."""
    verdict = "significant" if contrast.significant else "n.s."
    return (
        f"{contrast.name}: {_fmt_interval(contrast.interval)}, p={contrast.p_value:.4f} "
        f"({verdict}, {contrast.direction}, n={contrast.n_left}/{contrast.n_right})"
    )


def _contrast_lines(*contrasts: Contrast | None) -> list[str]:
    """One formatted line per contrast that was actually computed (not gated to `None`)."""
    return [_fmt_contrast(c) for c in contrasts if c is not None]


def _mapping_lines(mapping: dict[str, Contrast]) -> list[str]:
    """One formatted line per contrast in a `{key: Contrast}` mapping, key-sorted."""
    return [_fmt_contrast(c) for _, c in sorted(mapping.items())]


def _check_lines(checks: dict[str, BinomialResult]) -> list[str]:
    """One line per manipulation/representation check, key-sorted."""
    return [
        f"- `{key}`: {b.successes}/{b.trials} ({'PASS' if b.passed else 'FAIL'})"
        for key, b in sorted(checks.items())
    ]


def _note_lines(notes: list[str]) -> list[str]:
    """Render a report's free-text notes as Markdown block quotes."""
    return [f"> {note}" for note in notes]


def _render_utility(report: utility.UtilityReport) -> list[str]:
    """Render one model's Experiment 3 factorial outcomes."""
    lines = [f"## {report.model_key}", "", f"Probes: {report.probes}", ""]
    lines.extend(_check_lines(report.checks))
    if report.unrun:
        lines.append(f"Unrun: {report.unrun}")
    lines.append("")
    lines.extend(
        _contrast_lines(report.u2, report.u3, report.u3_neutral, report.u1, report.frame_effect)
    )
    lines.append(f"U2 ordered pattern U+ > U0 > U-: {report.u2_ordered}")
    lines.append(f"U2 established (U7 trigger): {report.u2_established}")
    lines.append("")
    lines.extend(_note_lines(report.notes))
    lines.append("")
    return lines


def _render_locus(report: utility.LocusReport) -> list[str]:
    """Render one model's `U7` objective-locus control."""
    lines = [
        f"### {report.model_key} — U7 objective locus",
        "",
        f"Triggered: {report.triggered}",
        "",
    ]
    lines.extend(_check_lines(report.checks))
    lines.extend(_contrast_lines(report.beta_inner, report.beta_outer, report.conflict))
    lines.append(f"Reading: {report.reading}")
    lines.append("")
    lines.extend(_note_lines(report.caveats))
    lines.extend(_note_lines(report.notes))
    lines.append("")
    return lines


def _render_u2_rerun(report: utility.U2RerunReport) -> list[str]:
    """Render one model's stage-11 `U2` rerun (E3d)."""
    lines = [
        f"### {report.model_key} — U2 rerun (stage 11)",
        "",
        f"Probes: {report.probes}, instances: {report.instances}",
        "",
    ]
    lines.extend(_check_lines(report.checks))
    lines.extend(_contrast_lines(report.u2, report.salience_plus, report.salience_minus))
    lines.extend(_mapping_lines(report.u3_by_utility))
    lines.append(f"Ordered U+ > U0 > U-: {report.ordered}")
    lines.append(f"U2 established (U7 trigger): {report.u2_established}")
    lines.append("")
    lines.extend(_note_lines(report.notes))
    lines.append("")
    return lines


def _render_provenance(report: provenance.ProvenanceReport) -> list[str]:
    """Render one model's Experiment 4 outcomes, across every regime present."""
    lines = [f"## {report.model_key}", "", f"Probes: {report.probes}", ""]
    lines.extend(_check_lines(report.checks))
    if report.unrun:
        lines.append(f"Unrun: {report.unrun}")
    lines.append("")
    lines.extend(_mapping_lines(report.derivation))
    lines.extend(_mapping_lines(report.context))
    lines.extend(_mapping_lines(report.regime_effect))
    lines.append(f"Reading: {report.reading}")
    lines.append("")
    lines.extend(_note_lines(report.notes))
    lines.append("")
    return lines


def _render_recipient(report: recipient.RecipientReport) -> list[str]:
    """Render one model's Experiment 5 outcomes, by polarity."""
    lines = [f"## {report.model_key}", "", f"Probes: {report.probes}", ""]
    lines.extend(_check_lines(report.checks))
    if report.unrun:
        lines.append(f"Unrun: {report.unrun}")
    lines.append("")
    lines.append(f"Belief ordered: {report.belief_ordered}")
    lines.extend(_mapping_lines(report.r1))
    lines.extend(_mapping_lines(report.r2_ip))
    lines.extend(_mapping_lines(report.r2_pk))
    lines.extend(_mapping_lines(report.r3))
    lines.extend(f"{_fmt_contrast(c)} equivalent={eq}" for _, (c, eq) in sorted(report.r4k.items()))
    lines.extend(f"{_fmt_contrast(c)} equivalent={eq}" for _, (c, eq) in sorted(report.r4r.items()))
    lines.append(f"Replicated: {report.replicated}")
    lines.append(f"Reading: {report.reading}")
    lines.append("")
    lines.extend(_note_lines(report.notes))
    lines.append("")
    return lines


def run_utility(args: argparse.Namespace, resamples: int) -> int:
    """Analyse Experiment 3 -- the factorial, its `U7` locus control, and the `U2` rerun.

    Returns:
        A process exit code; 0 both on success and when Experiment 3's records are absent.
    """
    if not tier1.records_available(args.utility):
        print(f"\n(no Experiment 3 records at {args.utility}; that experiment is UNRUN)")
        return 0
    records = tier1.load_records(args.utility)
    lines = ["# Experiment 3 — utility misattribution (regenerated)", ""]
    for model in sorted({r["model_key"] for r in records}):
        report = utility.analyse(records, model, CHECK_THRESHOLD, resamples, SEED)
        lines.extend(_render_utility(report))
        locus = utility.analyse_locus(
            records,
            model,
            CHECK_THRESHOLD,
            resamples,
            SEED,
            u2_established=report.u2_established,
        )
        lines.extend(_render_locus(locus))
    if tier1.records_available(args.utility_rerun):
        rerun = tier1.load_records(args.utility_rerun)
        for model in sorted({r["model_key"] for r in rerun}):
            rerun_report = utility.analyse_u2_rerun(rerun, model, CHECK_THRESHOLD, resamples, SEED)
            lines.extend(_render_u2_rerun(rerun_report))
    else:
        lines.append(f"(no U2 rerun records at {args.utility_rerun}; E3d is UNRUN)")
        lines.append("")
    rendered = "\n".join(lines)
    args.utility_out.parent.mkdir(parents=True, exist_ok=True)
    args.utility_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    print(f"\nwritten: {args.utility_out}")
    return 0


def run_provenance(args: argparse.Namespace, resamples: int) -> int:
    """Analyse Experiment 4, if its stage-9 records are present.

    Unions the stage-9 records with the stage-10 re-rendered and truncated re-scores when
    those files are present, so `derivation`/`context`/`regime_effect` see every regime the
    published table reports -- the same union `analyse` itself expects, since regime is a
    field on each record rather than a property of which file it came from. Unlike `cli.py`'s
    Experiment-1 unions, this does not assert the three files share one pipeline fingerprint:
    they do not, by design (`experiment4/results/FINDINGS.md`: the stage-10 passes carry a
    later fingerprint than stage 9, because they were run after two rendering fixes).

    Returns:
        A process exit code; 0 both on success and when stage-9 records are absent.
    """
    if not tier1.records_available(args.provenance):
        print(f"\n(no Experiment 4 records at {args.provenance}; that experiment is UNRUN)")
        return 0
    records = tier1.load_records(args.provenance)
    for extra in (args.rerendered, args.truncated):
        if tier1.records_available(extra):
            records += tier1.load_records(extra)
    lines = ["# Experiment 4 — provenance misattribution (regenerated)", ""]
    for model in sorted({r["model_key"] for r in records}):
        report = provenance.analyse(records, model, CHECK_THRESHOLD, resamples, SEED)
        lines.extend(_render_provenance(report))
    rendered = "\n".join(lines)
    args.provenance_out.parent.mkdir(parents=True, exist_ok=True)
    args.provenance_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    print(f"\nwritten: {args.provenance_out}")
    return 0


def run_recipient(args: argparse.Namespace, resamples: int) -> int:
    """Analyse Experiment 5, if its records are present.

    Returns:
        A process exit code; 0 both on success and when Experiment 5's records are absent.
    """
    if not tier1.records_available(args.recipient):
        print(f"\n(no Experiment 5 records at {args.recipient}; that experiment is UNRUN)")
        return 0
    records = tier1.load_records(args.recipient)
    lines = ["# Experiment 5 — recipient misattribution (regenerated)", ""]
    for model in sorted({r["model_key"] for r in records}):
        report = recipient.analyse(records, model, CHECK_THRESHOLD, resamples, SEED)
        lines.extend(_render_recipient(report))
    rendered = "\n".join(lines)
    args.recipient_out.parent.mkdir(parents=True, exist_ok=True)
    args.recipient_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    print(f"\nwritten: {args.recipient_out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the Experiment 3/4/5 analyses with pinned resamples and seed, and write reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--utility", type=Path, default=DEFAULT_UTILITY)
    parser.add_argument("--utility-rerun", type=Path, default=DEFAULT_UTILITY_RERUN)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--rerendered", type=Path, default=DEFAULT_RERENDERED)
    parser.add_argument("--truncated", type=Path, default=DEFAULT_TRUNCATED)
    parser.add_argument("--recipient", type=Path, default=DEFAULT_RECIPIENT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--utility-out", type=Path, default=EXPERIMENT3_ROOT / "results" / "RESULTS_UTILITY.md"
    )
    parser.add_argument(
        "--provenance-out",
        type=Path,
        default=EXPERIMENT4_ROOT / "results" / "RESULTS_PROVENANCE.md",
    )
    parser.add_argument(
        "--recipient-out",
        type=Path,
        default=EXPERIMENT5_ROOT / "results" / "RESULTS_RECIPIENT.md",
    )
    args = parser.parse_args(argv)

    if not args.config.is_file():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 2

    thresholds = load_thresholds(args.config)
    resamples = int(thresholds.get("bootstrap_resamples", 10000))
    print(
        f"resamples={resamples} (from {args.config}, key 'bootstrap_resamples'), seed={SEED}, "
        f"check_threshold={CHECK_THRESHOLD}\n"
    )

    codes = [
        run_utility(args, resamples),
        run_provenance(args, resamples),
        run_recipient(args, resamples),
    ]
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())
