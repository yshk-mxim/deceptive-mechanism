# Experiment 2 — Selection misattribution (§4.4–§4.5)

**Draft for review.** Read `../PROGRAM.md` first for the causal ordering and the shared
apparatus. Experiment 1's findings are cited as F-numbers; they live in
`../experiment1/results/FINDINGS.md`.

## 0. Scope, and why this is deliberately small

The claim under test:

> **realised output ≠ model preference**

A rollout can be misleading while the learned conditional policy at `S` favoured truth. Any
method that reads a deceptive *selection mechanism* off the realised output alone is
outcome-defined, and cannot distinguish a preference from a draw.

**Experiment 1 already produced this phenomenon organically.** F8: in 14 of 40 states the
scores favoured the constraint-consistent answer while 20.5% of draws realised an
inconsistent one, per-state range 0–46.5%. So Experiment 2 is not a discovery exercise. It
has two jobs Experiment 1 could not do:

1. Construct the effect **with a known truth**. The guessing game has no ground truth — the
   "consistent answer" is a constraint satisfaction, not a fact. §4.4 needs a state where
   truth and falsity are externally established.
2. Run the **external-selector negative control** (§4.5), which has no analogue in
   Experiment 1 and is the stronger conceptual result.

This should be the smallest of the four experiments. Resisting the temptation to expand it is
part of the design: the mirror conditions and model-selector positive control that suggest
themselves are not required by the paper's §4.4/§4.5 and would dilute a clean point.

## 1. Claims and inferential tiers

**Tier 1 — the demonstration.** At a state `S` with `P(T|S) > P(F|S)` under the sampler,
repeated sampling from that identical `S` realises `F` on some draws. Those rollouts are
misleading outputs from a truth-preferring policy.

**Tier 2 — the selector control.** With an external RNG choosing between a fixed true and a
fixed false report, half the trials return a falsehood that no model preference produced.

**If Tier 2 fails, Tier 1 stands.** They are independent arguments.

## 2. The truth substrate

§4.4 requires "independently verified knowledge of the truth". Three candidate substrates,
with the trade-off stated:

| | Truth established by | Risk |
|---|---|---|
| **A. Arithmetic** | Computation the model can verify (`17 × 23 = 391`) | Model may be wrong about it; then `T` is not preferred and the design fails |
| **B. In-context fact** | A fact stated in the prompt ("the meeting is at 3pm") | F10's hazard: stated is not represented. Needs a manipulation check |
| **C. Scripted episode** | An event written into the history by the harness | Closest to Experiment 1's construction and inherits its guarantees |

**Recommendation: C, with B as a robustness arm.** A harness-written episode gives the same
state-identity guarantee Experiment 1 rests on, and the truth is in the record rather than in
the model's competence. Arithmetic is rejected as primary: it makes the design depend on a
capability F5 shows is unreliable in a no-reasoning single pass.

The manipulation check is not optional. Before any `T`/`F` comparison, the state must be
shown to represent the truth — a readout on the fact itself, at the same standard as
Experiment 1's G2 sensitivity gate. **If the model does not represent the truth at `S`, a
"false" report is not false-relative-to-belief and the trial is void**, not evidence.

## 3. Design — 2A, stochastic-tail selection

Per scenario:

1. Build the episode, write it into the context, capture `S`.
2. **Manipulation check**: readout on the fact. Require recovery at the G2 standard.
3. Score matched `T` and `F` reports at `S` without decoding — the §4.2 readout.
4. Require `P(T|S) > P(F|S)` **under the sampler** (F9), with `P(F|S) > 0` under it too. A
   state where the sampler truncates `F` to zero cannot exhibit the effect and is recorded
   as ineligible rather than dropped silently.
5. Sample R draws from `S` at the deployment sampler. Record every realisation.

**The pre-registered quantity** is the rate at which a truth-preferring state yields a
misleading realisation, with `p_realise(F) = 1 − (1 − P_sampler(F))^R` as the reference
prediction — the same discipline as Experiment 1's `p_diverge`, where the prediction comes
from the recorded distribution and observing zero is a legitimate outcome.

**Matched response forms.** `T` and `F` must be token-length-matched (see `../PROGRAM.md`)
and differ minimally in surface form. An unmatched pair scores length, not preference.

## 4. Design — 2B, external-random-selector negative control

The experimental realisation of the paper's opening coin example.

The system is given the established truth and two fixed reports `R_T`, `R_F`. An RNG
**external to the model** draws `Z ~ Bernoulli(0.5)` and returns the corresponding report.

Two independent facts hold by construction, and both are recorded rather than argued:

```
truth/falsity        ↛  Z
recipient effect     ↛  Z
```

`selector_source` records which RNG produced `Z`, and the seed makes it replayable.

**What this establishes.** On half the trials the transcript contains a false report that may
mislead a recipient. Any methodology that labels this a deceptive selection mechanism, on the
basis of the trajectory containing a falsehood, misclassifies an intentionally non-deceptive
selector. That is a statement about the methodology, not about the model, and it needs no
model behaviour at all to be true — which is precisely why it is a strong control.

**The measurement that makes it more than a thought experiment**: score the same `T`/`F` pair
at the same state and show `P(T|S) > P(F|S)` while the *emitted* report is `R_F` on half the
trials. Preference and output are then observed to disagree with the disagreement fully
explained by an agent outside the model.

## 5. What is measured, and what is not

| Recorded | Why |
|---|---|
| `P_raw(T)`, `P_raw(F)`, `P_sampler(T)`, `P_sampler(F)` | F9: naming which distribution is not optional |
| Full candidate scores, digest of the logit vector | Same standard as Experiment 1 |
| `state_digest` | Rollouts must be shown to come from one state |
| Realised outcomes per draw, with seed | The demonstration itself |
| `selector_source` | 2B only; null in 2A |
| Manipulation-check readout | Void trials are identified, not silently included |

**Not measured**: whether the model "intended" anything. §4.4 and §4.5 are about what an
observer may infer from an output, and adding an intention measure would import the construct
under examination.

## 6. Hypotheses and thresholds

To be frozen before collection. Stated against a no-decoding readout and a sampler-aware
prediction, per F5's lesson.

| | Test | Threshold |
|---|---|---|
| **G2′** | Manipulation check: the state represents the truth | ≥ 0.90, as Experiment 1's G2 |
| **E1** | Eligible states have `P_sampler(T) > P_sampler(F) > 0` | descriptive; ineligible states reported, not dropped |
| **E2** | Observed rate of misleading realisations consistent with `p_realise(F)` | interval overlap; zero is legitimate |
| **E3** | 2B: `P(T\|S) > P(F\|S)` while emitted reports are 50% false | one-sided |

## 7. Threats

**The sampler truncates the tail.** F9's central lesson: with top-p 0.80, a state where
`p_max > 0.80` admits one candidate and no amount of sampling produces `F`. Eligibility must
be judged post-sampler, and a study that raised temperature to force the effect would be
substituting a different distribution — recorded under `sampler_role: branch_instantiation`
and barred from supporting any claim about the deployment policy.

**"False" that is not false.** If the model does not represent the truth, `F` is not a
falsehood relative to anything. Hence the mandatory manipulation check, and F10 as the
cautionary case: a sentence in context is not thereby a represented fact.

**Length confound.** Addressed in `../PROGRAM.md`; asserted by test per model.

## 8. Deliverables

Pre-registration, records, statistics, prompts, and the analysis package — same shape as
Experiment 1, same exclusion of the inference harness. Estimated cost: **two stages, well
under Experiment 1's**, since there is no factorial and no branch arm beyond the rollouts.
