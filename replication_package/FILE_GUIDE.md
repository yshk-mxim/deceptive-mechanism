# File guide

What every file in this package is, where it sits, and how it is used. Written file by file, and
used as an audit while writing: each claim below was checked against the artifact rather than
recalled, and what that turned up is recorded at the end.

The short version of how to use the package: read an experiment's `results/FINDINGS.md` for what
was found, its `PREREGISTRATION*.md` for what was promised beforehand, `PROMPTS.md` for what the
models were shown, and run the analysis to regenerate the numbers yourself.

## Top level

| file | what it is | how it is used |
|---|---|---|
| `README.md` | entry point for the repository | start here; it says where to look for what |
| `DISCLAIMER.md` | statement that every organisation, person and address in the scenarios is fictional | read before the prompts, which name a firm and email addresses that look real and are not |
| `LICENSE` | MIT | covers the code and documents here |

## Package-level documents

| file | lines | what it is | how it is used |
|---|---|---|---|
| `REPLICATION_GUIDE.md` | 318 | the directory map and the regeneration commands | the other half of this file: it maps each headline number to the function that produces it |
| `PROMPTS.md` | 1213 | every prompt the models were shown, regenerated from the scenario code | the authority on wording; the appendix in the paper is an excerpt of it |
| `PROGRAM.md` | 389 | why the experiments are ordered as they are, and the standing methodological commitments | read it to see what each experiment is allowed to conclude |
| `CONSTRUCT_VALIDITY.md` | 104 | an external review of the prompts against the experiment plans | it records two places where the review changed what may be claimed |
| `KNOWN_DEFECTS.md` | 136 | every instrument defect found in the pre-release audit, with its exposure | read it before quoting any Experiment 4 figure; it states which two defects move a number and which way |
| `FILE_GUIDE.md` | - | this file | orientation, and a checklist for auditing the package |

## The analysis package

`replication_package/experiment1/analysis/` holds the code that turns records into numbers. It
lives under `experiment1` for historical reasons and serves all five experiments.

| module | lines | covers | what it computes |
|---|---|---|---|
| `__init__.py` | 3 | package marker | modules are imported by name |
| `bare_value.py` | 310 | Experiment 1, bare-value arm | asks for the value rather than the index, so a positional artefact cannot explain recovery |
| `cli.py` | 281 | entry point, Experiments 1 and 2 | regenerates their numbers with resamples from config and seed 0 |
| `cli_345.py` | 346 | entry point, Experiments 3 to 5 | the same for the q_D experiments; added so their parameters are recorded |
| `judging.py` | 387 | report labelling | two conventions for calling a generated report deceptive, and the gap between them |
| `metrics.py` | 268 | shared metrics | divergence probability, total variation, KL in bits, effective sampling distribution |
| `provenance.py` | 483 | Experiment 4 | the 4A1/4A2/4E ladder, the derivation contrast, and the reasoning regimes |
| `recipient.py` | 664 | Experiment 5 | the knowledge and reachability axes, the control arms, and the equivalence tests |
| `selection.py` | 442 | Experiment 2 | eligibility under the deployment sampler, the observed false-report rate, the external selector |
| `stats.py` | 443 | shared statistics | cluster bootstrap, Clopper-Pearson, Holm-Bonferroni, manipulation checks, equivalence |
| `tier1.py` | 865 | Experiment 1, Tier 1 | the commitment gates and contrasts: determinism, sensitivity, constraint tracking, and T2-T5 |
| `tier23.py` | 875 | Experiment 1, Tiers 2 and 3 | paraphrase agreement, Luo et al.'s override probes R0 and R0S kept separate, truncation |
| `turn_resolved.py` | 347 | Experiment 1, Luo's per-turn metrics | Drift Rate and per-step KL, run with the positive control their design lacked |
| `utility.py` | 1104 | Experiment 3 | q_D by payoff and recipient level, the U contrasts, the locus cells, and the stage 11 rerun |

Each module has a test file of the same name under `tests/`. The suite is not a formality:
every test builds records the way the harness builds them and asserts the quantity the module is
supposed to compute, because an earlier fixture encoded the analysis's assumption instead of the
harness's behaviour and the two agreed while both were wrong.

| supporting file | what it is |
|---|---|
| `pyproject.toml` | the package definition and its pinned dependencies |
| `uv.lock` | the resolved dependency set, so the environment is reproducible |
| `Makefile` | `make analysis` and `make analysis-345` run the two entry points |
| `cosmic-ray.toml` | configuration for the exhaustive mutation run |
| `tests/test_schema_contract.py` | asserts the record schema the harness writes and the analysis reads are the same contract |

## The experiments

Each directory holds the same five kinds of thing: a plan, a pre-registration, the prompts'
provenance where relevant, the records with their manifests, and the results. The results
directory always contains `FINDINGS.md`, which is the document to read.

### Experiment 1 — Deferred commitment — does a later report retrieve an earlier choice?

| file | size | what it is |
|---|---|---|
| `APPENDIX_TECHNICAL.md` | 304 lines | the implementation detail behind the apparatus, including the faults found and fixed |
| `DATASHEET.md` | 117 lines | the dataset described in datasheet form: how it was collected, what it contains, its limits |
| `EXPERIMENT1_PLAN.md` | 1050 lines | the design document, written before the pre-registration |
| `METHODOLOGY.md` | 226 lines | how the apparatus works, and how faithfully it reproduces Luo et al. |
| `PREREGISTRATION.md` | 181 lines | what was promised before collection: hypotheses, thresholds, and the analysis plan |
| `README.md` | 147 lines | orientation for this experiment's directory |
| `configs/experiment1.toml` | 131 lines | configuration: thresholds, sampler settings, bootstrap resamples |
| `data/manifests/stage00_env_gate.json` | manifest | provenance for `stage00_env_gate`: model revisions, package versions, pipeline fingerprint |
| `data/manifests/stage01_tier1.json` | manifest | provenance for `stage01_tier1`: model revisions, package versions, pipeline fingerprint |
| `data/manifests/stage02_tiers23.json` | manifest | provenance for `stage02_tiers23`: model revisions, package versions, pipeline fingerprint |
| `data/manifests/stage03_bare_value.json` | manifest | provenance for `stage03_bare_value`: model revisions, package versions, pipeline fingerprint |
| `data/manifests/stage04_turn_resolved.json` | manifest | provenance for `stage04_turn_resolved`: model revisions, package versions, pipeline fingerprint |
| `data/records/bare_value_records.jsonl.gz` | 960 records | the collected measurements, one JSON object per line |
| `data/records/tier1_records.jsonl.gz` | 2400 records | the collected measurements, one JSON object per line |
| `data/records/tiers23_records.jsonl.gz` | 6400 records | the collected measurements, one JSON object per line |
| `data/records/turn_resolved_records.jsonl.gz` | 1920 records | the collected measurements, one JSON object per line |
| `prompts/LICENSING.md` | 116 lines | where each prompt came from and what may be done with it |
| `prompts/readout.toml` | 141 lines | configuration: thresholds, sampler settings, bootstrap resamples |
| `results/FINDINGS.md` | 927 lines | **the results.** Opens with a headline, states what is and is not established, and lists numbers that must not be quoted |
| `results/RESULTS.md` | 109 lines | generated by the analysis; regenerate it to check the numbers reproduce |
| `results/RESULTS_BARE_VALUE.md` | 57 lines | generated by the analysis; regenerate it to check the numbers reproduce |
| `results/RESULTS_TIER23.md` | 131 lines | generated by the analysis; regenerate it to check the numbers reproduce |
| `results/RESULTS_TURN_RESOLVED.md` | 104 lines | generated by the analysis; regenerate it to check the numbers reproduce |
| `results/tier1_results.json` | 410 lines | see the file |
| `schemas/probe_record.v1.json` | 57 fields | the record schema, the one contract shared by the harness and the analysis |

### Experiment 2 — Selection misattribution — does a realised output identify a preference?

| file | size | what it is |
|---|---|---|
| `EXPERIMENT2_PLAN.md` | 156 lines | the design document |
| `PREREGISTRATION.md` | 110 lines | what was promised before collection: hypotheses, thresholds, and the analysis plan |
| `data/manifests/stage00_env_gate.json` | manifest | provenance for `stage00_env_gate`: model revisions, package versions, pipeline fingerprint |
| `data/manifests/stage05_selection.json` | manifest | provenance for `stage05_selection`: model revisions, package versions, pipeline fingerprint |
| `data/records/selection_records.jsonl.gz` | 2080 records | the collected measurements, one JSON object per line |
| `results/FINDINGS.md` | 173 lines | **the results.** Opens with a headline, states what is and is not established, and lists numbers that must not be quoted |
| `results/RESULTS.md` | 79 lines | generated by the analysis; regenerate it to check the numbers reproduce |

### Experiment 3 — Utility misattribution — does the recipient's state or the payoff change the preference?

| file | size | what it is |
|---|---|---|
| `EXPERIMENT3_PLAN.md` | 834 lines | the design document |
| `PREREGISTRATION.md` | 291 lines | what was promised before collection: hypotheses, thresholds, and the analysis plan |
| `PREREGISTRATION_U2_RERUN.md` | 92 lines | the second pre-registration, for the payoff rerun, committed before its collection |
| `data/manifests/stage06_rotated_gate.json` | manifest | provenance for `stage06_rotated_gate`: model revisions, package versions, pipeline fingerprint |
| `data/stage07_utility.json` | manifest | provenance for `stage07_utility`: model revisions, package versions, pipeline fingerprint |
| `data/stage11_utility_rerun.json` | manifest | provenance for `stage11_utility_rerun`: model revisions, package versions, pipeline fingerprint |
| `data/utility_records.jsonl.gz` | 4776 records | the collected measurements, one JSON object per line |
| `data/utility_rerun_records.jsonl.gz` | 2592 records | the collected measurements, one JSON object per line |
| `results/FINDINGS.md` | 746 lines | **the results.** Opens with a headline, states what is and is not established, and lists numbers that must not be quoted |
| `results/RESULTS_UTILITY.md` | 112 lines | generated by the analysis; regenerate it to check the numbers reproduce |

### Experiment 4 — Emergence and provenance — was the strategy derived or supplied?

| file | size | what it is |
|---|---|---|
| `EXPERIMENT4_PLAN.md` | 376 lines | the frozen design; this experiment has no pre-registration, and says so |
| `data/provenance_records.jsonl.gz` | 2592 records | the collected measurements, one JSON object per line |
| `data/rerendered_records.jsonl.gz` | 864 records | the collected measurements, one JSON object per line |
| `data/stage09_provenance.json` | manifest | provenance for `stage09_provenance`: model revisions, package versions, pipeline fingerprint |
| `data/stage10_rerendered.json` | manifest | provenance for `stage10_rerendered`: model revisions, package versions, pipeline fingerprint |
| `data/stage10_truncated.json` | manifest | provenance for `stage10_truncated`: model revisions, package versions, pipeline fingerprint |
| `data/truncated_records.jsonl.gz` | 824 records | the collected measurements, one JSON object per line |
| `results/FINDINGS.md` | 603 lines | **the results.** Opens with a headline, states what is and is not established, and lists numbers that must not be quoted |
| `results/RESULTS_PROVENANCE.md` | 73 lines | generated by the analysis; regenerate it to check the numbers reproduce |

### Experiment 5 — Recipient-belief mechanism — does the recipient effect run through belief?

| file | size | what it is |
|---|---|---|
| `EXPERIMENT5_PLAN.md` | 430 lines | the design document |
| `PREREGISTRATION.md` | 311 lines | what was promised before collection: hypotheses, thresholds, and the analysis plan |
| `data/recipient_records.jsonl.gz` | 5760 records | the collected measurements, one JSON object per line |
| `data/stage08_recipient.json` | manifest | provenance for `stage08_recipient`: model revisions, package versions, pipeline fingerprint |
| `results/FINDINGS.md` | 378 lines | **the results.** Opens with a headline, states what is and is not established, and lists numbers that must not be quoted |
| `results/RESULTS_RECIPIENT.md` | 81 lines | generated by the analysis; regenerate it to check the numbers reproduce |
| `results/RUN1_FAILED.md` | 95 lines | why the first collection was discarded rather than patched |


## How the analysis works

### The shape of every experiment

One shape runs through all five. The harness builds a transcript, captures the model state at the
measurement point, restores that state independently for each readout, appends a probe, and scores
matched candidate answers from the logits without decoding anything. What lands in a record is a
distribution over candidates at one state, not a generated sentence. Everything the analysis does
starts from that.

```
scenario code  ->  captured state  ->  one branch per probe  ->  candidate logits  ->  record
                                                                                        |
                                          FINDINGS.md  <-  analysis module  <-----------+
```

### From a record to a number

A record carries `candidates`, `candidate_logprobs`, `conditional` (the candidate-normalised
distribution), and `consistent_set`. That last field means two different things by design, and
it is the single most important thing to understand before reading the code:

- **Experiments 2 to 5**: it names the one **truthful** candidate index. The endpoint is
  `q_D = P(D) / (P(D) + P(T))`, the normalised preference for the concealing answer, computed in
  `utility._q_deny` and its siblings.
- **Experiment 1**: it holds the **set** of candidate indices still consistent with the constraints
  stated so far. There is no truthful index because there is no target; the quantity of interest is
  how much mass sits inside the set, computed in `metrics.consistent_mass`.

Reading one as the other silently inverts every contrast, which is why ten call sites were audited
against this distinction and why three modules assert the set has exactly one element before
indexing it.

### The functions that carry the results

| what you want | call | notes |
|---|---|---|
| Experiment 1's gates and contrasts | `tier1.analyse_model(records, model, thresholds, samplers, resamples, seed)` | returns `ModelReport`; `render_report` formats it |
| Tier 2 and the Luo replication | `tier23.analyse(records, model, thresholds, resamples, seed)` | `R0` and `R0S` stay separate throughout |
| the bare-value arm | `bare_value.analyse(...)` | asks for the value, not the index |
| Luo's per-turn metrics | `turn_resolved.analyse(joined, model, resamples, seed)` | needs Tier-1 and turn records joined |
| Experiment 2 | `selection.analyse(records, model, thresholds, samplers, resamples, seed)` | eligibility depends on the sampler, so `samplers` is not optional |
| Experiment 3 | `utility.analyse(records, model, check_threshold, resamples, seed)` | plus `analyse_locus` for the objective-locus cells and `analyse_u2_rerun` for stage 11 |
| Experiment 4 | `provenance.analyse(records, model, check_threshold, resamples, seed)` | pass the rerendered and truncated records in as well |
| Experiment 5 | `recipient.analyse(records, model, check_threshold, resamples, seed)` | |

Every one of these takes `resamples` and `seed` explicitly. Nothing in the package draws a random
number without a seed passed in from a caller.

### The shared machinery

`stats.py` holds everything statistical, and four of its functions decide most verdicts:

- `cluster_bootstrap(clusters, statistic, resamples, seed)` resamples **whole scenario instances**,
  never individual probes. Probes from one instance share a scenario and a captured state, so
  resampling them independently would understate the variance. Paired contrasts resample the two
  arms jointly through `_bootstrap_difference`.
- `manipulation_check(hits, n, threshold)` judges a representation check on the **observed rate**.
  Its docstring explains why: judging a check by a confidence bound turns a stated 0.90 into an
  effective 0.98, so a perfect small sample could fail. Confirmatory gates use `binomial_gate`,
  which does judge by the bound; checks do not.
- `bootstrap_p_value(draws, resamples, one_sided=)` scores a directional contrast on the
  one-sided tail. The doubled two-sided tail handed a directional test its smallest p-value when
  the effect ran the wrong way, which once let six wrong-way contrasts through a Holm family.
- `holm_bonferroni(p_values, alpha)` corrects within a pre-registered family, stepping down and
  halting at the first failure.

`metrics.py` holds the distribution quantities: `p_diverge`, `total_variation`,
`kl_divergence_bits`, `consistent_mass`, and `effective_sampling_distribution`, which applies a
model's own top-p, top-k and min-p to a distribution to say what the deployment sampler could
actually have realised. That last one decides Experiment 2's eligibility and therefore its
headline rate.

### Configuration

`experiment1/configs/experiment1.toml` is the one source of truth, read by both entry points.

| section | keys | what they control |
|---|---|---|
| `[models.*]` | `repo_id`, `chat_template`, `enable_thinking`, `sampler_temperature`, `sampler_top_p`, `sampler_top_k`, `sampler_min_p` | which checkpoint, how it renders a chat, and the deployment sampler. The sampler keys decide Experiment 2's eligibility, so they are read with a hard subscript: a missing key raises rather than silently meaning "no truncation" |
| `[design]` | `games`, `probe_points`, `question_turns`, `rollout_samples`, `candidate_count` | the shape of Experiment 1: 40 games, two probe points, five question turns, 200 draws per rollout, ten candidates |
| `[analysis]` | `recovery_acc_min`, `consistent_mass_min`, `false_recovery_max`, `tost_tv_margin`, `tost_kl_margin_bits`, `alpha`, `bootstrap_resamples` | the pre-registered thresholds and the resample count. `bootstrap_resamples = 10000` is what both CLIs read, so the two experiments' families cannot drift apart |
| `[determinism]` | `restorations`, `stratified_states` | how hard the state-restoration gate was pushed: 50 restorations of the same state |
| `[runtime]` | `master_seed`, `hf_hub_offline` | the collection seed recorded in every manifest, and the flag that kept the run offline |

Thresholds are loaded by `cli.load_thresholds`, which `cli_345` imports rather than duplicating.

### Running it

From `replication_package/experiment1/analysis`:

```
uv sync --all-extras            # the environment, pinned by uv.lock
uv run pytest                   # the invariants the analysis must satisfy
python -m deceit_analysis.cli       # Experiments 1 and 2
python -m deceit_analysis.cli_345   # Experiments 3, 4 and 5
```

Both entry points read `bootstrap_resamples` from the config and fix `seed=0`, then write
`RESULTS*.md` beside each `FINDINGS.md`. They do not overwrite `FINDINGS.md`, which is written by
hand and is where the interpretation lives.

Records ship gzipped and `tier1.load_records` reads either form, falling back to the `.gz` sibling
when a plain `.jsonl` is named. `tier1.records_available` is the matching existence check; use it
rather than `Path.exists`, because a guard that checks only the plain path reports a shipped
experiment as unrun.

### What the tests are for

`tests/` mirrors the modules one for one. The tests are not coverage theatre: each builds records
**the way the harness builds them** and asserts the quantity the module is supposed to compute.
That convention exists because an early fixture encoded the analysis's own assumption instead, so
the test and the code agreed while both were wrong about which index was truthful.
`test_schema_contract.py` pins the record schema that the harness writes and the analysis reads.

A second layer sits outside the package: a hand-curated mutation gate introduces a specific
semantic defect, one at a time, and requires some test to fail. A test suite that passes against a
deliberately broken analysis is not testing the analysis.

## References to files that are not here

Some documents name modules of the collection harness: scenario builders, pipeline stages, the
cache and scoring engine, the mutation tooling. **The harness is deliberately not shipped.** It is
bound to one machine and one accelerator stack, and what reproduction needs is the records it wrote
plus the code that turns them into numbers, both of which are here. Those names are given so a
reader can see which component produced what, not as links. The same applies to references to the
paper's own appendix sources and to the author's working documents: a todo list, two critiques of a
superseded draft of the manuscript, and a plan for an experiment that is not part of this paper.
None bears on reproducing a reported number.

## Using this file as a check

The point of writing down what each file does is that the writing forces a look. If you are
auditing this package, these are the checks worth running, all of which were run while this file
was written:

1. **Every record file's fingerprint appears in a manifest.** Eleven record files, thirteen results
   manifests plus one gate manifest. Passed.
2. **No record file mixes fingerprints or schema versions.** A file that did would be two runs
   concatenated. Passed on all eleven.
3. **Every analysis module has a test file of the same name.** Passed, except `cli.py`, whose
   behaviour is exercised end to end by regenerating the results rather than by unit tests.
4. **Every file named in a document exists, or is named in the section above.** This one failed
   when first run, and the failures were fixed: references to the working documents the release
   omits, and one to a provenance file that never existed under that name.
5. **The documented commands run.** From `replication_package/experiment1/analysis`:
   `uv sync --all-extras`, then `uv run pytest`, then `python -m deceit_analysis.cli` and
   `python -m deceit_analysis.cli_345`. All four succeed against the package as shipped.
6. **The regenerated results match the shipped ones.** Both entry points write `RESULTS*.md` beside
   each `FINDINGS.md`; a diff against the committed copies should be empty.
7. **Every record validates.** All 31,168 records were checked against
   `probe_record.v1.json`: no missing required field, no field outside the schema, every
   `conditional` non-negative and summing to 1, every `consistent_set` index inside the candidate
   list, no positive log-probability. Passed.
8. **No record is a duplicate measurement.** Apparent collisions on model, game, probe point and
   readout key resolve on a further field, and it is worth knowing which: in Experiment 1 a state
   carries both its plain readout and its 200-draw rollout arm, separated by `sampler_role`; in
   Experiment 4 a state carries three sampled reasoning trajectories, separated by `sampler_seed`.
   Those three share a scenario instance, so the cluster bootstrap holds them in one cluster rather
   than treating them as independent observations.
9. **Every interval in a findings file traces to the analysis.** Of 31 stated across Experiments
   3 to 5, 25 name a point estimate the entry point computes and all 25 reproduce exactly; 16 of
   those carry bounds differing by at most 0.0019, from figures computed before the seed was
   pinned. The other 6 are quantities the entry point does not emit, four of them the
   objective-locus contrasts the analysis refuses to compute because their trigger is closed.
10. **The endpoint is recomputable from the raw scores.** For all 31,168 records, `conditional` is
    exactly the renormalised softmax of `candidate_logprobs`, to zero deviation. An auditor can
    rebuild `q_D` from the log-probabilities without trusting the harness's normalisation.
11. **Branches share their captured state.** Every probe branching from one state carries that
    state's `state_digest`, with no disagreement anywhere. Reporting probes and representation
    checks share a state by design, which is what makes a check evidence about that state.
12. **No logit digest is shared by two different prompts.** Grouping all 31,168 records by
    captured state and probe gives 27,292 distinct digests and no collision across prompts. Repeats
    occur only where one prompt was scored twice for two arms.

Check 4 is the one that found real problems, and it is the one most worth repeating after any edit.

## What is not in this package, and where it went

| omitted | why |
|---|---|
| the collection harness | bound to one machine; the records and manifests are what reproduction needs |
| superseded and failed collections | the findings and pre-registrations record what each was and why it was set aside; no reported number depends on the files |
| the project's todo list and two working critiques of a superseded draft | project management, not evidence |
| a plan for a further experiment | not part of this paper |
