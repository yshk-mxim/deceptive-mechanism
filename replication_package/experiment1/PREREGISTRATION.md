# Pre-registration — Experiment 1

**Experiment:** Exact-State Deferred-Commitment Test (paper §4.1–§4.3)
**Config digest:** the frozen parameter set is `configs/experiment1.toml`; its hash is
recorded in every run manifest under `config_digest`.

## 0. When the parameters were frozen

The design, conditions, tier structure and every threshold below were frozen in
`EXPERIMENT1_PLAN.md` and `configs/experiment1.toml` **before any measurement ran**. Each run
manifest carries a `config_digest` tying it to that frozen parameter set, so the freeze is
verifiable rather than asserted. This document was written up afterwards and introduces
nothing the runs could have influenced.

## 1. Hypothesis

> **No run-specific difference between otherwise identical runs can exist in the identical
> pre-selection state.**

The state may contain a distribution over candidates, a representation of the instruction,
and latent structure not measured here. What it cannot contain is a commitment to one
candidate in one branch and a different one in another, because the branches share it by
construction. The experiment asks whether retrospective probing converts that single common
state into apparently different prior commitments.

**Explicitly not claimed:** that language models lack belief- or target-like
representations. Full logits characterise preference under one elicitation; they do not
exhaust internal representation.

## 2. Design

Two models: `mlx-community/gemma-4-26B-A4B-it-qat-8bit` and
`sprisa/Qwen3.6-27B-MLX-8bit-MTP`, 8-bit, non-thinking.

Tier-1 grid: 2 models × 40 games × 2 probe points (early, late), all Regime D, with
conditions C0 (commitment framing), C1 (target injected), C2 (target and reason injected)
and C4 (distractor) as **state-matched** controls, and 3 fixed neutral readout paraphrases.
Branch arm on C0 and C1: R = 200 draws at the model-card deployment sampler, then one greedy
retrospective probe and one greedy explanation probe per realised branch.

Every assistant turn before the reveal is written by the harness, so the pre-reveal state is
identical across branches by construction.

## 3. Gates

A gate failure changes what may be concluded, not merely a number.

| Gate | Criterion |
|---|---|
| **G1** determinism | Identical snapshot + identical prompt ⇒ identical full-logit digest across K = 50 restorations |
| **G2** sensitivity | `RecoveryAcc(C1) ≥ 0.90` |
| **G3** competence | `ConsistentMass(C0, Regime D) ≥ 0.80` |

**If G2 fails, no null-shaped result is interpretable as evidence of absence.** It is
reported as an apparatus failure, never as a finding.

## 4. Pre-registered tests

Verdicts use the **confidence-interval bound**, not the point estimate, so an underpowered
cell cannot pass on a lucky proportion. Exact (Clopper–Pearson) intervals at 95%.

### Tier 1 — the causal demonstration

| # | Test | Threshold |
|---|---|---|
| T1 | Observed divergence consistent with `p_diverge` implied by the recorded distribution | descriptive; see §5 |
| T2 | `RetrospectiveFollowsRealized` | ≥ 0.90 |
| T3 | `RealizedChoiceRationalizationRate` | ≥ 0.90 |
| T4 | `ReasonRecovery(C2) > ReasonRecovery(C0)` | one-sided |
| T5 | `FalseRecoveryRate(C4)` | ≤ 0.15 |

### Tier 2 — mechanism characterisation

`H_readout(C0) − H_readout(C1) ≥ 1.0` bit; `ParaAgree(C1) > ParaAgree(C0)` against the
IID-resample chance baseline; `TurnJSD(C0) > TurnJSD(C1)`; and two equivalence tests —
`TV(C0, C3) ≤ 0.10` and `PriorKL ≤ 0.15` bits.

**A Tier-2 failure does not disturb Tier 1.** Tier 1 rests on state identity, not on
explaining the readout distribution.

### Tier 3 — replication and diagnostic analysis of Luo et al.

Reported in a clearly labelled appendix: `OverrideTV > 0.10` for their SUDO-override probe
framing, and `TurnKL_top20 > TurnKL` for their top-20/−9999 truncation.

## 5. Divergence is predicted, not required

For R draws from recorded candidate probabilities, `p_diverge(R) = 1 − Σ pᵢᴿ`. Whether
branching ought to occur is fixed by the recorded distribution.

- The canonical branch test runs at the deployment sampler, R = 200, reporting the measured
  distribution alongside `p_diverge(200)`.
- **Observing no divergence is a legitimate outcome**, not an apparatus failure. Where
  `p_max` is near 1, a near-deterministic policy is itself a finding about the learned
  conditional policy.
- Raising temperature is **not** a remedy: it substitutes a different distribution. Any
  raised temperature is recorded as `sampler_role: branch_instantiation`, is valid for the
  retrospective measurement (branches still share one state), and may **never** support a
  claim about branching frequency under normal policy.

## 6. Equivalence margins, fixed on substantive grounds

Margins are **not** derived from the pilot. A margin estimated from the behaviour being
evaluated means "what the pilot produced", not "scientifically negligible".

- **TV ≤ 0.10.** Total variation is the largest shift in probability for any event; over ten
  candidates this is at most a 0.1 shift for any single one — below the level at which a
  reader would change their description of which candidate is favoured.
- **KL ≤ 0.15 bits.** Against `log₂ 10 ≈ 3.32` bits of maximum entropy, under 5% of the
  range.

The pilot informs variance and power only. If precision cannot resolve these margins, the
remedy is more games, never a wider margin.

## 7. Analysis rules

- **`candidate_mass` is a second outcome, never an exclusion filter.** Filtering on it would
  condition the analysis on the dependent variable. Low-mass probes are flagged in the
  record, never dropped.
- **Explanation scoring is rule-based only.** No LLM judge: using a second language model to
  adjudicate whether an explanation counts as a rationalisation would reproduce, inside the
  instrument, the interpretive move the paper criticises. Raw explanations ship verbatim.
- Cluster bootstrap resamples **games**, not probes.
- Holm–Bonferroni within each tier's family, α = 0.05.
- Every reported result carries its tier.

## 8. Stopping rule and deviations

No interim peeking drives a design change. Items that fail to run are reported as UNRUN and
excluded from denominators, never silently dropped. Every pre-registered test is reported,
including those that came out against expectation.

**A deviation is a change that knowledge of the outcomes could have influenced** — a moved
threshold, a dropped condition, an analysis chosen after seeing which way it went. Getting
the apparatus to work is not a deviation, and recording it as one would bury the deviations
that matter.

**Deviations to date: none.** No threshold, hypothesis or analysis rule has changed since the
freeze.

**Corrections and one retraction, none of which changes a threshold, hypothesis or rule, are recorded in `results/FINDINGS.md`:** `F13` retracted (a keying bug in the override contrast; restated as `F16` on the corrected instrument); the Tier-3 probe `R0` corrected from Luo et al.'s Listing 3 clause to Listing 1's, with Listing 3 retained as `R0S` and Tier 3 re-collected; `F15` un-pooled (`R0` reported alone); `G3` and `T4` re-implemented as the quantities this document specifies; `T9` re-collected after `C3` was made to differ from `C0` in exactly one message. Summarised in the paper's Appendix C, deviations.

Three instrument corrections, disclosed because they touch conditions rather than plumbing,
and none informed by an outcome. **C3** was rendered as a single user turn against a
thirteen-turn C0, so it did not implement its own stated definition — "the same Q/A content,
differing only in framing" — and the comparison it exists to make was not the comparison being
computed. It now matches C0's structure exactly. **C6** was added as a structure-matched
prior, because C5 is a two-message prompt by construction and cannot be compared to a
thirteen-message C0 without the same confound; C5 is retained unchanged and still reported.
**C2** drew its injected reason uniformly from four options regardless of which index had
been injected, so most C2 games asserted something false — *"your secret choice is index 7.
You chose it because it is the first option in the list."* C2's definition is a target **and a
reason**, and a reason that contradicts its own target is not one; the condition was
confounding recoverability with willingness to repeat a falsehood, which this design cannot
separate. Reasons are now drawn from those that hold of the injected index.

All three were found by reading rendered transcripts and the code that produces them, not
results. All three were corrected before the collection that is reported here, and the
affected data was recollected rather than reanalysed.

Runs made before the instrument was working are not results and are not treated as such.
Three commissioning faults were found and fixed — a checkpoint whose weights were corrupted
at load, a chat template that suppressed reasoning in the prompt but not in the model, and
stale bytecode from the mutation-testing harness. Those runs never measured the intended
experiment. They are retained as `data/records/tier1_records_INVALID_*.jsonl` for
inspection, and the faults are documented in `APPENDIX_TECHNICAL.md` because they are
genuine upstream bugs others will hit — not because they bear on the pre-registration.

## 9. Weaknesses disclosed in advance

- Gemma is quantisation-aware trained and Qwen is post-training quantised; there is no QAT
  Qwen 3.6. Family is confounded with quantisation method, forbidding cross-family
  comparison of absolute logit values. The primary claim is within-model.
- The candidate scheme uses single-token indices, following Luo et al. for comparability. An
  index is a pointer, so the readout may partly measure pointer stability. The fixed-width
  bare-value arm is the check on that, and it is Tier 2.
- Contexts stay under Gemma's 1024-token sliding window so no rotation occurs. Results
  therefore speak to the windowed regime; the rotated regime is validated separately for
  Experiment 3.
- Two models is the minimum the paper's §4.8 asks for. Per-model analysis is primary; no
  pooled claim is made without homogeneity.
