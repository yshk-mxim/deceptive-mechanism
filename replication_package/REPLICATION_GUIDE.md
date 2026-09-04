# Replication guide — where everything is, and how to regenerate it

> **Fictional entities.** Every organisation, person, email address and ticker below is fictional
> and refers to no real party. The trading scenario reconstructs the environment published by
> Scheurer et al. (arXiv:2311.07590), whose paper prints `WhiteStone`, `Alpha`, `Amy`, `Sally`,
> `LING` and the addresses `amy@whitestone.com` and `sally@whitestone.com`; reproducing them is
> what makes this a replication rather than a different experiment. The 23 further surfaces are
> ours, and their addresses are derived at run time from invented firm names. Some of those domains
> happen to be registered by unrelated parties. Nothing here describes, alleges or implies conduct
> by any real company, person or domain holder, and no address was ever contacted. See
> `DISCLAIMER.md`.

This is the authoritative file-level map of the replication package. It was this guide of the
paper until the 2026-09-02 release restructure, which moved package documentation out of the
manuscript and into the repository; the paper now carries a one-sentence pointer here instead.
Nothing was dropped in the move.


A reader's map: what each file is for, what the shared record schema means field by field,
what a manifest records, and which function in the shipped analysis package regenerates
which experiment's headline numbers.

## Directory tree

Cache/build directories (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`,
`.hypothesis`, `.ruff_cache`) are omitted throughout. Groups of same-shaped data files are
collapsed to one line with a count.

```
replication_package/
├── PROMPTS.md                          rendered prompt appendix this document cross-checks against (the paper's Appendix B)
├── PROGRAM.md                          cross-experiment ordering and shared apparatus
├── CONSTRUCT_VALIDITY.md               external review of PROMPTS.md against the experiment plans
├── experiment1/
│   ├── README.md                       package overview, maps to paper §4.1-4.3
│   ├── EXPERIMENT1_PLAN.md             design rationale, frozen before collection
│   ├── PREREGISTRATION.md              frozen hypotheses/thresholds; names the config digest
│   ├── METHODOLOGY.md                  enough detail to rebuild the scenarios/measurements from scratch
│   ├── APPENDIX_TECHNICAL.md           describes the inference harness precisely (harness itself not shipped)
│   ├── DATASHEET.md                    Datasheets-for-Datasets description of the record files
│   ├── configs/experiment1.toml        the frozen design + analysis-threshold values (source for the paper's Appendix B, E1 renders)
│   ├── prompts/readout.toml            E1's readout/explanation prompt bank (source for the paper's Appendix B, R0-R8/X1)
│   ├── prompts/LICENSING.md            per-prompt provenance/licence, incl. the Luo et al. R0/R0S attribution
│   ├── schemas/probe_record.v1.json    JSON Schema for probe_record.v1 (57 properties, matches records.py exactly)
│   ├── data/manifests/*.json (5)       one per E1 pipeline stage: run id, fingerprint, git commit, packages, seed (see below)
│   ├── data/records/*.jsonl.gz (4)     tier1/tiers23/bare_value/turn_resolved records. INVALID_*/SUPERSEDED_* runs are described but not redistributed; see "What is not redistributed" in README.md
│   ├── results/FINDINGS.md             the living findings log, with scope limits, written for incorporation into the paper
│   ├── results/RESULTS*.md (4) + tier1_results.json   Tier-1/Tier-2-3/bare-value/turn-resolved headline numbers, machine-readable + prose
│   └── analysis/                       `deceit_analysis` — the portable, model-free analysis package (see below)
│       ├── src/deceit_analysis/*.py (13)   one module per experiment's headline numbers, plus metrics/stats/judging/cli/cli_345 shared helpers
│       ├── tests/*.py (13)                 one test module per analysis module, incl. a schema-contract test
│       └── pyproject.toml, Makefile, cosmic-ray.toml, uv.lock   packaging, dependency gate, and mutation-testing config
├── experiment2/
│   ├── EXPERIMENT2_PLAN.md
│   ├── PREREGISTRATION.md
│   ├── data/manifests/*.json (2)       stage00_env_gate, stage05_selection
│   ├── data/records/selection_records.jsonl
│   ├── results/FINDINGS.md
│   └── results/RESULTS.md
├── experiment3/
│   ├── EXPERIMENT3_PLAN.md
│   ├── PREREGISTRATION.md
│   ├── data/manifests/stage06_rotated_gate.json   the rotated-regime determinism gate, not a results manifest
│   ├── data/stage07_utility.json + utility_records.jsonl   manifest + records, kept flat in `data/` rather than `data/records/` (layout note below)
│   ├── PREREGISTRATION_U2_RERUN.md     the stage 11 rerun, committed before its collection
│   ├── data/stage11_utility_rerun.json + utility_rerun_records.jsonl   the pre-registered `U2` rerun (E3d): 2592 records in their own file, so they cannot pool with the factorial
│   └── results/FINDINGS.md
├── experiment4/
│   ├── EXPERIMENT4_PLAN.md             frozen design; **no** PREREGISTRATION.md (see Pre-registrations below)
│   ├── data/stage09_provenance.json + stage10_truncated.json   manifests, flat in `data/`
│   ├── data/provenance_records.jsonl + truncated_records.jsonl   records, flat in `data/`
│   └── results/FINDINGS.md
├── experiment5/
│   ├── EXPERIMENT5_PLAN.md
│   ├── PREREGISTRATION.md
│   ├── data/stage08_recipient.json     current manifest. The failed run's manifest is described but not redistributed
│   ├── data/recipient_records.jsonl.gz
│   ├── results/FINDINGS.md
│   └── results/RUN1_FAILED.md          what went wrong with run 1 and why it was rerun rather than patched
```

**Layout note.** Experiments 1 and 2 keep `data/manifests/` and `data/records/` as separate
subdirectories; Experiments 3, 4, and 5 keep both manifests and record files flat inside
`data/`. This is a real inconsistency in the package's own directory conventions, not a typo
in this map — verified against the actual filesystem layout, not assumed from a pattern.

## The `probe_record.v1` schema

One JSON object per line, one line per measurement at one captured state
(`harness/src/deceit_harness/io/records.py`, `ProbeRecord`). Fields a given experiment never
populates are reserved and nullable rather than invented per experiment, because a schema change
after collection starts either breaks comparability or forces a migration. Fifty-two fields were
fixed before Experiment 1 was collected; five (`inner_utility`, `outer_utility`,
`reach_condition`, `control_arm`, `control_level`) were added, nullable, for Experiment 3's
objective-locus control and for Experiment 5, so Experiment 1 and 2 records carry 52 keys and
Experiment 4 and 5 records carry all 57. Experiment 3's carry 54: the three fields added for
Experiment 5's control arms (`reach_condition`, `control_arm`, `control_level`) are absent, and no
analysis reads them on an Experiment 3 record. Experiments 1 and 2 carry 52. The schema declares
57 properties and requires 24; the rest are nullable by design, so a record is valid with fewer
keys than the analysis happens to use. All 57 fields, in declaration order:

| Field | Meaning |
|---|---|
| `schema` | Schema version tag, `"probe_record.v1"`. |
| `run_id` | Groups every record written by one stage invocation. |
| `pipeline_fingerprint` | Hash of the source that produced this record — part of the provenance chain (with `state_digest`/`logit_digest` below). |
| `model_key` | Config key of the model measured. |
| `model_revision` | HF snapshot revision of that model. |
| `tier` | Inferential tier: 1 = causal demonstration, 2 = mechanism, 3 = Luo-appendix replication. |
| `condition` | Experimental condition (e.g. `C0`..`C6`, or an Experiment 3/4-style cell tag). |
| `regime` | Constraint regime (`D`/`U` in E1; reused loosely elsewhere, e.g. `direct`/`reasoning` semantics live in E4's `condition`/`regime` pairing). |
| `game_id` | Scenario instance identifier. |
| `probe_point` | Where the state was captured (e.g. `early`, `late`, `turn1`..`turn4`, or a role tag like `manipulation_check`/`query`/`external_selector`). |
| `readout_key` | Which readout prompt produced this record. |
| `readout_framing` | `neutral` or `sudo_override` (E1), reused as the polarity tag (`positive`/`negative`) in E3/E4/E5. |
| `state_digest` | Fingerprint of the pre-branch state — provenance chain. |
| `state_tokens` | Token count of the captured state. |
| `logit_digest` | Fingerprint of the full float32 logit vector — provenance chain. |
| `candidates` | Candidate strings, in a fixed order. |
| `candidate_logprobs` | Unconditional log-probabilities, aligned to `candidates`. |
| `candidate_mass` | Probability the full vocabulary puts on the candidate set. **A second, always-reported outcome — never used to filter or exclude a probe.** |
| `conditional` | Distribution over candidates given that the answer is one of them. |
| `entropy_bits` | Entropy of `conditional`. |
| `p_max` | Top-1 conditional probability. |
| `topk_tokens` | Top-k token ids at the answer position. |
| `topk_logprobs` | Log-probabilities aligned to `topk_tokens`. |
| `consistent_set` | In Experiment 1, indices consistent with **all** the scripted answers, regardless of probe point (a *set*, since Regime U's target need not be narrowed to one). In the `q_D` experiments (E2–E5), the same field instead names the single **truthful** index — the eventual/correct answer, never the deceptive one, and never a filter on which probes are analysed. |
| `running_consistent_set` | Indices still consistent with the answers given *up to* this probe point; equals every candidate at `early`, equals `consistent_set` at `late`. Says whether a given turn carried information. |
| `option_values` | Bare-value arm only: the fixed-width values actually shown, in list order. Null in the index arm. |
| `injected_index` | Target instantiated in hidden context (E1 C1/C2), else null. |
| `injected_reason` | Reason instantiated in hidden context (E1 C2), else null. |
| `distractor_index` | Distractor target (E1 C4), else null. |
| `sampler_role` | `canonical` (deployment sampler; the only role that can support a claim about branching frequency under normal policy), `branch_instantiation` (raised temperature, used only to obtain multiple branches for retrospective measurement), `reasoning` (E4's stage-9 trajectory generation), `reasoning_truncated` (E4's stage-10 re-scoring of the same trajectories, cut before their first committing sentence), or `none`. |
| `sampler_temperature` | Temperature actually used, or null if nothing was sampled. |
| `sampler_top_p` | Nucleus threshold actually used, or null. |
| `sampler_top_k` | Top-k cutoff actually used, or null. |
| `sampler_min_p` | Relative floor actually used, or null. |
| `sampler_seed` | Seed for the draw, so it is replayable from the record alone. |
| `rollout_samples` | Number of draws taken. |
| `realized_counts` | Realised candidate → how many times it was drawn. |
| `p_diverge` | Divergence probability implied by `conditional` at `rollout_samples`. |
| `retrospective` | Per realised branch, what the model reported when asked what it chose. |
| `explanations` | Per realised branch, the greedy explanation text (E1's X1 confabulation measure). |
| `post_selection_entropy_bits` | Per branch, readout entropy once that branch's own token is in history. |
| `post_selection_p_max` | Per branch, top-1 readout probability once that branch's token is in history. |
| `post_selection_argmax` | Per branch, which candidate the post-selection readout favours. |
| `injected_history_id` | Reserved (E2-4 branch injection); nullable, unpopulated by E1. |
| `injected_branch_label` | Reserved ("trade occurred" / "did not occur"); nullable. |
| `action_candidates` | Reserved: matched legal/prohibited actions; nullable. |
| `recipient_state` | Reserved: manager-ignorant/manager-informed style state, reused by E3/E5's recipient axis; nullable outside those. |
| `utility_condition` | Reserved: utility-manipulation condition tag, populated by E3; nullable outside it. |
| `inner_utility` | E3's `U7` only — what concealment is worth to the **simulated character**. Null outside the objective-locus subexperiment. |
| `outer_utility` | E3's `U7` only — what concealment is worth to the **model's own stated experimental score**. Paired with `inner_utility` because one `utility_condition` field cannot express two objectives held by different actors. |
| `reach_condition` | E5 only — whether the report can reach the recipient's belief. **Its own field, deliberately not folded into `provenance_condition`**, which is reserved for E4's four provenance classes; overloading a reserved field with a second meaning is exactly what made `consistent_set` disagree between two code paths in an earlier draft, with nothing raised. |
| `control_arm` | E5 only — which semantic-language control a cell belongs to, or `treatment`. |
| `control_level` | The level of that control's clause; empty string for a treatment cell. |
| `persona_id` | Reserved: role-framing tag, reused by E3/E4's `persona` factor; nullable outside those. |
| `provenance_condition` | E4's provenance condition (`4A1`/`4A2`/`4E`), populated by `stage09_provenance._record` alongside `condition`, which carries the same tag, and `regime`, which carries the inference regime; nullable outside E4. |
| `selector_source` | E2's 2B arm only — identifies the external RNG (`blake2b_derived_rng_outside_model`); null for every model-sampled row, including 2A's. |
| `judge_labels` | Reserved: a *map*, not a scalar, because different judging conventions (e.g. whether vagueness counts as deception) can disagree, and the gap between them is itself a result. |

## The manifests

Every `*/data/*.json` manifest (one per pipeline stage) shares one shape, written by
`deceit_harness.io.manifest.build_manifest`. Example, `experiment1/data/manifests/stage01_tier1.json`:

```json
{
  "config_digest": "212327d12df3bd70b3fa2504663d8d08",
  "git_commit": "de900d63b3db532ee79d2eab8857eb29a37a2e25",
  "master_seed": 20260831,
  "packages": {"mlx": "0.31.2", "mlx-lm": "0.31.3", "mlx-metal": "0.31.2", "numpy": "2.5.2", "transformers": "5.10.0"},
  "payload": {"models": {"...": {"revision": "...", "seconds": 441.7, "states": 320, "weight_digest": "..."}},
              "records": 2400, "records_path": "runs/final8/tier1_records.jsonl", "run_id": "354d872e703a"},
  "pipeline_fingerprint": "3f3a07b4f6660939293d9ddb64eb4eec",
  "platform": "macOS-26.6.2-arm64-arm-64bit arm64",
  "python": "3.12.0",
  "stage": "stage01_tier1",
  "started_utc": "2026-09-01T20:34:50.656537+00:00"
}
```

- **`run_id`** — groups the JSONL records this invocation wrote (matches `run_id` in each
  `ProbeRecord`).
- **`pipeline_fingerprint`** — hash of the source that produced the run; matches
  `pipeline_fingerprint` in every record from that run and is the provenance link the
  analysis package's `assert_provenance_consistent` checks before trusting a records file.
- **`git_commit`** — the harness's commit at run time, with a `-dirty` suffix if the working
  tree had uncommitted changes. Checked across every manifest: seven carry the suffix — E1's
  `stage00_env_gate.json` and `stage04_turn_resolved.json`, E3's `stage06_rotated_gate.json`
  and `stage07_utility.json`, E4's `stage09_provenance.json`, and both E5 manifests. For those
  runs the commit hash alone does not identify the source; the `pipeline_fingerprint`, which
  hashes the source content itself, does, and it is what the analysis checks.
- **`packages`** — pinned versions of `mlx`, `mlx-lm`, `mlx-metal`, `numpy`, `transformers` —
  the runtime closure the harness actually ran under.
- **`master_seed`** — the top-level seed (`20260831` throughout); every per-probe seed is
  derived from it and the record's own identifying fields (`derive_seed` in
  `stage01_tier1.py`), so any draw is reproducible from the record alone without replaying
  the run.
- **`config_digest`** — hash of the frozen config (`configs/experiment1.toml`) the run used.
- **`payload`** — stage-specific: model revisions/weight digests, state/record counts, the
  records file path, and (for E3) `locus_states`/`longest_prompt_tokens`/`prompt_cap`.

## Which analysis function regenerates which experiment's numbers

All eight modules live in one package, `deceit_analysis`
(`experiment1/analysis/src/deceit_analysis/`), and share one JSONL loader,
`tier1.load_records(path)`. The package **never imports the harness** (`pyproject.toml`
comment, enforced by the dependency gate) — it needs only `numpy`/`scipy`, is meant to run on
any machine, and is the actual reproducibility claim the project makes about its numbers.

| Experiment | Module | Callable | Signature |
|---|---|---|---|
| E1 (Tier 1) | `tier1` | `analyse_model` | `(records, model_key, thresholds, samplers=None, resamples=2000, seed=0) -> ModelReport` |
| E1 (Tier 2/3) | `tier23` | `analyse` | `(records, model_key, thresholds, resamples, seed) -> Tier23Report` |
| E1 (bare-value arm) | `bare_value` | `analyse` | `(records, model_key, thresholds, resamples, seed) -> BareValueReport` |
| E1 (turn-resolved) | `turn_resolved` | `analyse` | `(records, model_key, resamples, seed) -> TurnReport` (no `thresholds` argument) |
| E2 | `selection` | `analyse` | `(records, model_key, thresholds, samplers, resamples, seed) -> SelectionReport` |
| E3 | `utility` | `analyse` (+ `analyse_locus` for U7) | `(records, model_key, check_threshold, resamples, seed) -> UtilityReport` |
| E4 | `provenance` | `analyse` | `(records, model_key, check_threshold, resamples, seed) -> ProvenanceReport` |
| E5 | `recipient` | `analyse` | `(records, model_key, check_threshold, resamples, seed) -> RecipientReport` |

`tier23`/`bare_value`/`turn_resolved` are invoked from `deceit_analysis.cli` (`python -m
deceit_analysis.cli --records ...`), Experiment 1's wired-up entry point; E2's
`selection.analyse` is also called from there via `--selection`. E3/E4/E5's `utility`,
`provenance`, and `recipient` modules have their own sibling entry point,
`deceit_analysis.cli_345` — added after a critical review noted that, unlike `cli.py`, nothing
in the package recorded the resamples and seed that produced their published intervals, so a
reviewer recomputing them got intervals differing by roughly 0.002 even though every point
estimate matched exactly. `cli_345` is a *sibling* module rather than an extension of `cli.py`
because Experiments 3-5's layout does not fit `cli.py`'s shape: flat `data/` directories
instead of `data/manifests/`+`data/records/` (the Layout note above), and an
`analyse(records, model_key, check_threshold, resamples, seed)` signature (all three modules
identical in shape) rather than a thresholds dict.

```
python -m deceit_analysis.cli_345
```

reproduces every Experiment 3/4/5 number this package can regenerate from the shipped JSONL,
one Markdown report per experiment (`experiment{3,4,5}/results/RESULTS_{UTILITY,PROVENANCE,
RECIPIENT}.md`, written next to each `FINDINGS.md`, not replacing it), run with the same
pinned parameters `cli.py` uses for E1/E2: `resamples` from `configs/experiment1.toml`'s
`bootstrap_resamples` (10000 — the same config, so there remains one source of truth for the
count) and `seed=0`, fixed the same way. `check_threshold=0.9` throughout, matching the value
`PREREGISTRATION_U2_RERUN.md` and every `test_utility.py`/`test_provenance.py`/
`test_recipient.py` call site already used. Running it twice reproduces every interval bound
and bootstrap p-value bit for bit. Verified against `FINDINGS.md`'s published intervals: E3d's
`U2` rerun reproduces exactly on both models (Gemma `+0.0463 [+0.0395, +0.0536]`, Qwen `+0.1865
[+0.1780, +0.1946]`) and point estimates reproduce exactly everywhere else checked (E3's
factorial `U2`/`U3`, E4's derivation/context/regime contrasts); a handful of already-published
interval *bounds* computed before this entry point existed carry the same sub-0.001 unrecorded
drift the review flagged — the exact gap this entry point closes going forward, not evidence
against these parameters (the one number the guide previously fixed a value for, E3d, matches
exactly; nothing here was tuned to force a match).

**Those published bounds are deliberately not regenerated, and will not be.** A full sweep of the
Experiment 3, 4 and 5 findings, run 2026-09-03, puts the scale exactly. Of 31 intervals stated
there, 25 name a point estimate the entry point also computes, and **every one of those 25 point
estimates is reproduced exactly**. Of those 25, **16 carry bounds that differ, by at most 0.0019**;
the rest agree to the digit. The remaining 6 are quantities the entry point does not emit: four are
the objective-locus contrasts, which the analysis refuses to compute because their pre-registered
trigger is closed and which the findings label exploratory for that reason, and two are diagnostic
breakdowns in Experiment 4 that exist only in its write-up.

An earlier version of this paragraph said two bounds differed by at most 0.0004. That was measured
on a sample rather than a sweep and understated the count; the figures above are the sweep.

Each pair is two valid bootstrap draws over the same records, so substituting one for the other
would change the published record without adding a fact. It would also misrepresent what this package can promise. The collection harness is
not shipped, so nothing here lets a reader regenerate the records themselves from the models; the
guarantee on offer is narrower and is the one that matters for checking the paper: **given these
records, this code reproduces every point estimate exactly, and with it every verdict, ordering and
significance decision.** Interval bounds carry Monte Carlo noise at the fourth decimal, which is
smaller than any effect the paper reports and far smaller than the run-to-run variation a reader
would meet if they re-collected the records on their own hardware. The paper quotes no confidence
interval, so nothing in the manuscript depends on this either way.

For a lower-level call, bypassing the entry point, the exact invocation pattern each module's
own test file and `cli_345` agree on:

```python
from pathlib import Path
from deceit_analysis import tier1, utility  # or provenance / recipient / selection / tier23 / bare_value

records = tier1.load_records(Path("experiment3/data/utility_records.jsonl"))
report = utility.analyse(records, "gemma4_26b_moe", check_threshold=0.9, resamples=10000, seed=0)

rerun = tier1.load_records(Path("experiment3/data/utility_rerun_records.jsonl"))
e3d = utility.analyse_u2_rerun(rerun, "gemma4_26b_moe", check_threshold=0.9, resamples=10000, seed=0)
```

`resamples` and `seed` are the cluster-bootstrap resample count and its RNG seed; E1's CLI
path reads `resamples` from the config's `bootstrap_resamples` (10000) and fixes `seed=0`.
Conditions whose manipulation checks fall below `check_threshold` are named in the report's
`unrun` list; the contrasts that involve them are **still computed and reported**, with the
caveat that they cannot be read as evidence about the manipulated factor (a statistical gate does
not decide which analysis runs — `PROGRAM.md`, "The statistics serve the phenomenon").

**The inference harness is referenced by module path, not shipped.** No copy of
`deceit_harness` exists anywhere under `replication_package/` — confirmed by search; the only
occurrences of the string `deceit_harness` there are two references by module path, in
`experiment1/EXPERIMENT1_PLAN.md` and `experiment1/prompts/LICENSING.md`.
`experiment1/APPENDIX_TECHNICAL.md` describes the harness precisely enough to reimplement it,
but the harness's own source (`harness/src/deceit_harness/`) sits outside this package. The
`deceit_analysis` package, by contrast, **is** shipped in full, with its own tests, packaging
metadata, and mutation-testing config — the part of the pipeline a third party can actually
run to reproduce a number, per `cli.py`'s own docstring: "Needs only Python, numpy and scipy:
no MLX, no model weights, no Apple hardware."

## Pre-registrations

Experiments 1, 2, 3, and 5 each carry a `PREREGISTRATION.md` (`experiment{1,2,3,5}/`),
frozen ahead of collection. **Experiment 4 does not.** Its design was frozen instead in
`experiment4/EXPERIMENT4_PLAN.md`, and the analysis rules were fixed after collection had
already begun — a deviation from the other four experiments' process, and one the project
records rather than obscures. The specifics of that deviation are being written up in a
dedicated section of `experiment4/results/FINDINGS.md` by another agent, concurrently with
this document; that section is not described here — see that file directly once it lands.
