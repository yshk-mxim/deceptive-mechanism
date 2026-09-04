# Copyright (c) 2026 Yakov P. Shkolnikov
# SPDX-License-Identifier: MIT
"""`cli_345` determinism: the same guarantee `cli.py` gives Experiments 1 and 2.

Every fixture is small and synthetic, matching the other modules' own test files
(`test_utility.py`, `test_provenance.py`, `test_recipient.py`), so these stay fast and never
touch the shipped (large) record files. The claim under test is not "the numbers are right" --
that belongs to those three files -- but that the entry point commits to one resamples count
and one seed, so running it twice reproduces the same interval bounds and p-values bit for
bit, and that the seed it pins is not inert (a no-op seed would make "pinning" it meaningless).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deceit_analysis import cli_345
from deceit_analysis import provenance as pv
from deceit_analysis import recipient as rc
from deceit_analysis import utility as ut

RESAMPLES = 200
INSTANCES = tuple(f"T{i:02d}" for i in range(5))


# ------------------------------------------------------------------ fixtures: Experiment 3


def utility_records() -> list[dict[str, Any]]:
    """5 instances x 3 utility levels, `U+` 0.8 vs `U-` 0.2 -- `test_utility.py`'s `spread()`.

    No check records: with none present nothing is gated, so `U2` is computed cleanly. `U3`
    needs a `K_AWARE` arm this fixture does not carry and is `None`, which
    `_bootstrap_difference` returns rather than raising on an empty arm.
    """
    levels = {ut.U_PLUS: 0.8, ut.U_ZERO: 0.5, ut.U_MINUS: 0.2}
    return [
        {
            "model_key": "m",
            "probe_point": ut.REPORT,
            "candidates": ["Yes", "No"],
            "conditional": [1.0 - q, q],
            "candidate_logprobs": [-0.1, -0.2],
            "consistent_set": [0],
            "candidate_mass": 0.99,
            "utility_condition": level,
            "recipient_state": ut.K_UNAWARE,
            "injected_branch_label": ut.TRADED,
            "game_id": f"{inst}-neutral-traded-{level}-{ut.K_UNAWARE}",
            "persona_id": "neutral",
            "readout_framing": ut.POSITIVE,
            "readout_key": "P1",
        }
        for inst in INSTANCES
        for level, q in levels.items()
    ]


def utility_records_with_variation() -> list[dict[str, Any]]:
    """Like `utility_records`, but the `U+ - U-` *difference* varies by instance.

    A constant level per instance makes every cluster resample compute the same mean
    regardless of which instances were drawn -- exactly what `utility_records` does, which is
    fine for the shape/byte-identity tests but would make a seed-sensitivity test vacuous. A
    constant *difference* is just as degenerate: `U2` pairs each instance's two arms in one
    resampled block (`_bootstrap_difference`), so a resample's estimate is the mean of that
    per-instance difference over whichever instances were drawn -- constant across instances,
    it is 0.5 no matter the draw. The difference itself has to vary by instance for the
    resample composition to move the estimate.
    """
    delta = {inst: 0.3 + 0.1 * i for i, inst in enumerate(INSTANCES)}
    plus = {inst: 0.5 + d / 2 for inst, d in delta.items()}
    minus = {inst: 0.5 - d / 2 for inst, d in delta.items()}
    return [
        {
            "model_key": "m",
            "probe_point": ut.REPORT,
            "candidates": ["Yes", "No"],
            "conditional": [1.0 - q, q],
            "candidate_logprobs": [-0.1, -0.2],
            "consistent_set": [0],
            "candidate_mass": 0.99,
            "utility_condition": level,
            "recipient_state": ut.K_UNAWARE,
            "injected_branch_label": ut.TRADED,
            "game_id": f"{inst}-neutral-traded-{level}-{ut.K_UNAWARE}",
            "persona_id": "neutral",
            "readout_framing": ut.POSITIVE,
            "readout_key": "P1",
        }
        for inst in INSTANCES
        for level, q in ((ut.U_PLUS, plus[inst]), (ut.U_MINUS, minus[inst]))
    ]


# ------------------------------------------------------------------ fixtures: Experiment 4


def provenance_records() -> list[dict[str, Any]]:
    """5 instances x 3 conditions x 2 regimes, all checks passing -- `test_provenance.py`'s
    `surface(NOT_DERIVED) + passing_checks()`, at a fifth of the instance count."""
    levels = {
        (pv.A1, pv.DIRECT): 0.75,
        (pv.A2, pv.DIRECT): 0.25,
        (pv.E, pv.DIRECT): 0.22,
        (pv.A1, pv.REASONING): 0.95,
        (pv.A2, pv.REASONING): 0.50,
        (pv.E, pv.REASONING): 0.05,
    }
    reports = [
        {
            "model_key": "m",
            "probe_point": ut.REPORT,
            "candidates": ["Yes", "No"],
            "conditional": [1.0 - q, q],
            "candidate_logprobs": [-0.1, -0.2],
            "consistent_set": [0],
            "candidate_mass": 0.99,
            "condition": condition,
            "regime": regime,
            "readout_framing": ut.POSITIVE,
            "readout_key": "P1",
            "game_id": f"{inst}-{condition}-{regime}",
            "explanations": {},
        }
        for inst in INSTANCES
        for (condition, regime), q in levels.items()
    ]
    checks = [
        {
            "model_key": "m",
            "probe_point": ut.CHECK,
            "candidates": ["Yes", "No"],
            "candidate_logprobs": [-0.1, -0.9],
            "consistent_set": [0],
            "condition": condition,
            "regime": regime,
            "readout_framing": "check",
            "readout_key": key,
            "game_id": f"{inst}-{condition}-{regime}",
            "explanations": {},
        }
        for inst in INSTANCES
        for condition in pv.LADDER
        for regime in (pv.DIRECT, pv.REASONING)
        for key in ("check_objective", "check_strategy", "check_circumstance")
    ]
    return reports + checks


# ------------------------------------------------------------------ fixtures: Experiment 5


def recipient_records() -> list[dict[str, Any]]:
    """5 instances x 3 knowledge levels x 2 reach levels x 2 polarities, checks passing --
    `test_recipient.py`'s `full(MECHANISM)`, without the belief/control arms that report is
    silent about when absent (`report.belief` and `report.r4k`/`r4r` simply stay empty)."""
    levels = {
        (rc.IGNORANT, rc.REACHABLE): 0.60,
        (rc.PARTIAL, rc.REACHABLE): 0.40,
        (rc.KNOWS, rc.REACHABLE): 0.20,
        (rc.IGNORANT, rc.UNREACHABLE): 0.20,
        (rc.PARTIAL, rc.UNREACHABLE): 0.20,
        (rc.KNOWS, rc.UNREACHABLE): 0.20,
    }
    reports = [
        {
            "model_key": "m",
            "probe_point": ut.REPORT,
            "candidates": ["Yes", "No"],
            "conditional": [1.0 - q, q],
            "candidate_logprobs": [-0.1, -0.2],
            "consistent_set": [0],
            "candidate_mass": 0.99,
            "recipient_state": knowledge,
            "reach_condition": reach,
            "control_arm": rc.TREATMENT,
            "control_level": "",
            "readout_framing": polarity,
            "readout_key": "P1" if polarity == ut.POSITIVE else "N1",
            "game_id": f"{inst}-{knowledge}-{reach}",
            "state_digest": f"{inst}:{knowledge}:{reach}:",
            "state_tokens": 300,
        }
        for inst in INSTANCES
        for (knowledge, reach), q in levels.items()
        for polarity in (ut.POSITIVE, ut.NEGATIVE)
    ]
    checks = [
        {
            "model_key": "m",
            "probe_point": ut.CHECK,
            "candidates": ["Yes", "No"],
            "candidate_logprobs": [-0.1, -0.9],
            "consistent_set": [0],
            "recipient_state": knowledge,
            "reach_condition": reach,
            "control_arm": rc.TREATMENT,
            "control_level": "",
            "readout_framing": "check",
            "readout_key": "check_truth",
            "game_id": f"{inst}-{knowledge}-{reach}",
            "state_digest": f"{inst}:{knowledge}:{reach}:",
            "state_tokens": 300,
        }
        for inst in INSTANCES
        for knowledge, reach in levels
    ]
    return reports + checks


# ------------------------------------------------------------------ CLI harness


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")


def _write_config(path: Path, resamples: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"[analysis]\nbootstrap_resamples = {resamples}\n", encoding="utf-8")


def _run(tmp_path: Path, resamples: int, out_suffix: str) -> Path:
    """Write the fixtures once and run `cli_345.main` against them, returning the output dir.

    Every output path is redirected under `tmp_path`: the entry point must never touch the
    repository's own `experiment{3,4,5}/results/` while under test.
    """
    utility_path = tmp_path / "utility_records.jsonl"
    provenance_path = tmp_path / "provenance_records.jsonl"
    recipient_path = tmp_path / "recipient_records.jsonl"
    config_path = tmp_path / "config.toml"
    out_dir = tmp_path / f"out_{out_suffix}"

    _write_jsonl(utility_path, utility_records())
    _write_jsonl(provenance_path, provenance_records())
    _write_jsonl(recipient_path, recipient_records())
    _write_config(config_path, resamples)

    code = cli_345.main(
        [
            "--utility",
            str(utility_path),
            "--utility-rerun",
            str(tmp_path / "does_not_exist.jsonl"),
            "--provenance",
            str(provenance_path),
            "--rerendered",
            str(tmp_path / "does_not_exist.jsonl"),
            "--truncated",
            str(tmp_path / "does_not_exist.jsonl"),
            "--recipient",
            str(recipient_path),
            "--config",
            str(config_path),
            "--utility-out",
            str(out_dir / "RESULTS_UTILITY.md"),
            "--provenance-out",
            str(out_dir / "RESULTS_PROVENANCE.md"),
            "--recipient-out",
            str(out_dir / "RESULTS_RECIPIENT.md"),
        ]
    )
    assert code == 0
    return out_dir


def test_the_pinned_parameters_match_the_documented_convention() -> None:
    """`REPLICATION_GUIDE.md`'s exact invocation: `check_threshold=0.9`, `seed=0`."""
    assert cli_345.CHECK_THRESHOLD == 0.9
    assert cli_345.SEED == 0


def test_resamples_come_from_the_shared_config_not_a_hardcoded_default(tmp_path: Path) -> None:
    """One source of truth: the same `bootstrap_resamples` key `cli.py` reads for E1/E2."""
    config_path = tmp_path / "config.toml"
    _write_config(config_path, 321)
    thresholds = cli_345.load_thresholds(config_path)
    assert int(thresholds["bootstrap_resamples"]) == 321


def test_running_the_entry_point_twice_is_byte_identical(tmp_path: Path) -> None:
    """The reproducibility guarantee itself: same resamples, same seed, same bytes out."""
    out_a = _run(tmp_path, RESAMPLES, "a")
    out_b = _run(tmp_path, RESAMPLES, "b")
    # Not merely identical because nothing was computed: each file carries a real contrast.
    markers = {
        "RESULTS_UTILITY.md": "U2:",
        "RESULTS_PROVENANCE.md": "derivation/direct:",
        "RESULTS_RECIPIENT.md": "R1:",
    }
    for name, marker in markers.items():
        text_a = (out_a / name).read_text(encoding="utf-8")
        text_b = (out_b / name).read_text(encoding="utf-8")
        assert text_a == text_b, f"{name} differed between two runs with identical parameters"
        assert marker in text_a


def test_the_written_report_reproduces_the_pinned_u2_rerun_shape(tmp_path: Path) -> None:
    """A sanity check on the rendering itself: `U2`'s point estimate is exactly the +0.6
    difference the fixture was built with (`U+` 0.8 minus `U-` 0.2), independent of resamples
    or seed -- only the interval around it is a function of those."""
    out = _run(tmp_path, RESAMPLES, "shape")
    text = (out / "RESULTS_UTILITY.md").read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("U2:")]
    assert len(lines) == 1
    assert "+0.6000" in lines[0]


def test_changing_the_seed_changes_the_bootstrap_interval_but_not_the_estimate() -> None:
    """The seed the entry point pins is load-bearing, not inert.

    Calling the underlying `analyse` with the entry point's own pinned `CHECK_THRESHOLD` and
    two different seeds must move the interval bounds -- otherwise "pinning" the seed would
    guarantee nothing a caller could not already get by accident.
    """
    records = utility_records_with_variation()
    report_a = ut.analyse(records, "m", cli_345.CHECK_THRESHOLD, RESAMPLES, seed=0)
    report_b = ut.analyse(records, "m", cli_345.CHECK_THRESHOLD, RESAMPLES, seed=1)
    assert report_a.u2 is not None
    assert report_b.u2 is not None
    assert report_a.u2.interval.estimate == report_b.u2.interval.estimate
    assert (report_a.u2.interval.low, report_a.u2.interval.high) != (
        report_b.u2.interval.low,
        report_b.u2.interval.high,
    )


def test_the_same_seed_reproduces_the_same_interval_directly() -> None:
    """The other half of the claim: two calls with the entry point's pinned seed agree
    exactly, with no entry point in between -- isolating the guarantee to `analyse` itself."""
    records = provenance_records()
    report_a = pv.analyse(records, "m", cli_345.CHECK_THRESHOLD, RESAMPLES, cli_345.SEED)
    report_b = pv.analyse(records, "m", cli_345.CHECK_THRESHOLD, RESAMPLES, cli_345.SEED)
    assert report_a.derivation[pv.DIRECT].interval == report_b.derivation[pv.DIRECT].interval
    assert report_a.derivation[pv.DIRECT].p_value == report_b.derivation[pv.DIRECT].p_value


def test_the_recipient_arm_runs_and_is_reproducible(tmp_path: Path) -> None:
    """Experiment 5's report renders, and reproduces exactly like the other two."""
    out_a = _run(tmp_path, RESAMPLES, "r1")
    out_b = _run(tmp_path, RESAMPLES, "r2")
    text_a = (out_a / "RESULTS_RECIPIENT.md").read_text(encoding="utf-8")
    text_b = (out_b / "RESULTS_RECIPIENT.md").read_text(encoding="utf-8")
    assert text_a == text_b
    assert "R1" in text_a


def test_an_absent_experiment_is_reported_and_does_not_fail_the_run(tmp_path: Path) -> None:
    """Matching `cli.py`'s optional-arm convention: a missing records file is a note, not an
    error, and the other experiments still run."""
    config_path = tmp_path / "config.toml"
    _write_config(config_path, RESAMPLES)
    utility_path = tmp_path / "utility_records.jsonl"
    _write_jsonl(utility_path, utility_records())
    out_dir = tmp_path / "out_missing"

    code = cli_345.main(
        [
            "--utility",
            str(utility_path),
            "--utility-rerun",
            str(tmp_path / "absent.jsonl"),
            "--provenance",
            str(tmp_path / "absent.jsonl"),
            "--recipient",
            str(tmp_path / "absent.jsonl"),
            "--config",
            str(config_path),
            "--utility-out",
            str(out_dir / "RESULTS_UTILITY.md"),
            "--provenance-out",
            str(out_dir / "RESULTS_PROVENANCE.md"),
            "--recipient-out",
            str(out_dir / "RESULTS_RECIPIENT.md"),
        ]
    )
    assert code == 0
    assert (out_dir / "RESULTS_UTILITY.md").is_file()
    assert not (out_dir / "RESULTS_PROVENANCE.md").exists()
    assert not (out_dir / "RESULTS_RECIPIENT.md").exists()


def test_a_missing_config_is_refused_rather_than_silently_defaulted(tmp_path: Path) -> None:
    """Silently falling back to 10000 would hide a broken `--config` path instead of failing
    loudly the way a reproducibility entry point should."""
    utility_path = tmp_path / "utility_records.jsonl"
    _write_jsonl(utility_path, utility_records())
    code = cli_345.main(
        [
            "--utility",
            str(utility_path),
            "--config",
            str(tmp_path / "does_not_exist.toml"),
        ]
    )
    assert code == 2
