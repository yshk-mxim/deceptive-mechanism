# Experiment 1 — Exact-State Deferred-Commitment Test

Replication package for Experiment 1 of *From Deceptive Outputs to Deceptive Mechanisms: A
Causal Framework for Language-Model Deception Research* (paper §4.1–§4.3).

## What this package is, and what it deliberately is not

It contains the **pre-registration, the data, the statistics, the prompts and the configs**.
It does not contain the inference harness.

That is a considered choice, not an omission. The harness is bound to one machine — Apple
Silicon, Metal, MLX 0.31.x, ~53 GB of local weights — and shipping it would imply a
portability it does not have. It is documented in `APPENDIX_TECHNICAL.md` and in the paper's
technical appendix instead.

What ships is what a third party can actually use:

```bash
cd analysis
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
python -m deceit_analysis.cli
```

That reproduces every Tier-1 number in the paper from the shipped JSONL, on any machine
with Python. No MLX, no weights, no Apple hardware. **That is the reproducibility claim.**

## Layout

```
PREREGISTRATION.md        design and thresholds, frozen before collection
DATASHEET.md              composition, collection, and inappropriate uses
METHODOLOGY.md            how scenarios and measurements are constructed
EXPERIMENT1_PLAN.md       the full design, including what was rejected and why
APPENDIX_TECHNICAL.md     the harness, described rather than shipped
results/FINDINGS.md       the experimental findings log, written for the paper
configs/experiment1.toml  every experimental parameter, with rationale and provenance tags
prompts/readout.toml      readout and explanation prompts, each with its hygiene check
data/records/tier1_records.jsonl        one record per probe (Tier 1)
data/records/tiers23_records.jsonl      mechanism and Luo-replication arms
data/records/bare_value_records.jsonl   the bare-value arm: no index labels, all 100
                                        values scored by prefix trie
data/records/turn_resolved_records.jsonl  the four intermediate probe points, for Luo
                                        et al.'s per-turn Drift Rate and KL
data/records/*_INVALID_*.jsonl          runs made before the instrument worked
data/records/*_SUPERSEDED_*.jsonl       runs of a working instrument later corrected by
                                        review; both classes are retained for inspection
                                        and excluded from every analysis (see below)
data/manifests/*.json     git commit, config digest, package versions, weight digests, seeds
analysis/                 the portable analysis package (pure Python; never imports the harness)
results/RESULTS.md        generated output
schemas/                  the record contract, validated from both QA stacks
```

## Provenance is enforced, not asserted

Every record carries the fingerprint of the source that produced it, and the analysis refuses
to run on a set whose fingerprint disagrees with its manifest, or on a file concatenating two
runs. That is not decorative: a manifest from one run was once shipped beside records from
another, and mixing a superseded run into a valid one is rejected on the real data.

Runs made before the instrument was working are retained as `*_INVALID_*.jsonl` rather than
deleted. They are not results, they are excluded from every analysis, and the faults that
produced them are documented in `APPENDIX_TECHNICAL.md`. Runs of a *working* instrument that
review later corrected are retained the same way, as `*_SUPERSEDED_pre_review.jsonl`.

**State identity is checked against the data, not only claimed.** Every record carries a
digest of the state it was measured at. The analysis refuses to run unless probes reported as
sharing a state carry one digest — and unless probes at different states carry different ones,
since a constant digest would pass the first check while measuring nothing.

## The inferential hierarchy — read this before the results

Three tiers with sharply different evidential status. A result at one tier says nothing
about another, and every reported number carries its tier.

**Tier 1 — the causal demonstration.** From one captured state `S`: record the full
candidate distribution without decoding; sample independently, giving realised answers
`A_i`; then, with `A_i` in history, ask what was chosen and why. If the retrospective report
and the rationale track `A_i` while `S` is provably identical across branches, those
branch-specific retrospective claims cannot establish branch-specific facts at `S`. C1 and
C2 show the same apparatus recovering a target, and a reason, that genuinely were in `S`.

**Tier 2 — mechanism characterisation.** Given that reports are generated rather than read
out, what distribution do they come from? C3 and C5 decompose the readout into in-context
constraints and generic prior. The **bare-value arm** belongs here too: it removes the index
labels entirely and scores every fixed-width value, so the phenomenon can be checked in an
answer space that contains no pointers.

**Tier 3 — replication and diagnostic analysis of Luo et al.** Their SUDO-override probe
framing and their top-20/−9999 truncation, as measured objects.

**What "replication" means here is bounded**, and `METHODOLOGY.md` states it precisely. Their
probe text, override clause, branch-probing design, candidate scheme and truncation rule are
reproduced from their published listings; their adaptive Guesser, their models, their entity
task and their fine-tuning arm are not. Tier 3 measures **their instrument in our paradigm on
our models**. Where it finds an effect, that effect is attributable to the instrument; where
it finds none, that is evidence about our setting and not a claim about their numbers.

**If Tier 2 fails, Tier 1 stands.** Tier 1 rests on state identity — a fact about the
construction — not on explaining the distribution.

## Two things to check before believing any Tier-1 number

**G2, the sensitivity gate.** If the readout cannot recover a target that really is in the
state (C1), then no null-shaped result is interpretable as evidence of absence. A G2 failure
is reported as an **apparatus failure**, never as a finding.

**`candidate_mass` is a second outcome, never a filter.** It is the share of probability the
full vocabulary puts on answering with a candidate at all. Filtering on it would condition
the analysis on the dependent variable. It earned its keep during the run: a mis-loaded
checkpoint showed mass around 0.06 against a working model's 0.9995, which is what exposed
the fault rather than hiding it.

## Divergence is predicted, not hoped for

For `R` draws from recorded candidate probabilities `p_i`, the probability of two or more
distinct outcomes is

```
p_diverge(R) = 1 - Σ_i p_i^R
```

Whether branching *ought* to occur is fixed by the recorded distribution, so **observing no
divergence is a legitimate outcome**, not an apparatus failure, and raising temperature is
not a remedy for it — it substitutes a different distribution. Any raised temperature is
recorded under `sampler_role: branch_instantiation` and may never support a claim about how
often branching occurs under the model's normal policy.

## Scope

This experiment tests one claim: **no run-specific difference between otherwise identical
runs can exist in the identical pre-selection state.** The state may contain a distribution
over candidates, a representation of the instruction, and latent structure we have not
measured; what it cannot contain is a commitment to 3 in one branch and 7 in another, since
the branches share it by construction.

It does **not** license any claim that language models lack belief- or target-like
representations. Full logits characterise preference under one elicitation; they do not
exhaust internal representation. Activation-level work is the stronger route and is out of
scope here.

## Licence

MIT. Prompts in `prompts/` are original to this work; `prompts/LICENSING.md` records the
provenance of anything derived from prior work.
