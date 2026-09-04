# Experiment 4 — Emergence and provenance misattribution (§4.7)

**Scope decided: 4A + 4E only.** 4B–4D are described here as **future stronger provenance
experiments, not required validations of the framework**. Read `../PROGRAM.md` first.

The honest headline of this experiment is a **negative epistemic result**, and that is the
point rather than a shortfall.

## 0. The question

Even granting deception-relevant selection, §2.5 asks a separate question:

> **Where did that strategy or objective come from?**

The paper names four provenance classes:

1. **Direct contextual instruction** — supplied in the prompt
2. **Direct or closely analogous training** — supplied by fine-tuning
3. **Compositional generalisation** from separately known components
4. **Out-of-distribution strategic generalisation**

and states the crucial rule: **where training provenance cannot be established because of
large-scale pretraining, the result is "unknown provenance", not "independently
originated".**

That rule is the finding this experiment mainly exists to make concrete, and the design
should be built to deliver it honestly rather than to escape it.

## 1. Why this needs the most design work

The first three experiments intervene on a *state*. This one has to intervene on **where a
capability came from**, and for a pretrained model the relevant history is unavailable. Two
consequences shape everything:

- **The positive conditions are constructible.** We can supply a strategy in context (4A) or
  by fine-tuning (4B) and then provenance is known by construction.
- **The negative condition is not.** For an unmodified base model, we cannot show a strategy
  never appeared in pretraining. No experiment on the model alone can.

So the design is: **contrast known contextual provenance with unresolved provenance**, and
use the contrast to show what an unidentifiable-provenance observation is worth. Calling it a
ladder whose rungs are all known would overstate it — 4A2's inferred tactic is deliberately
unresolved, and that is the point rather than a gap.

### Why the scope stops at 4A + 4E

**Experiments 1–3 strengthen this without making provenance the final step of a mandatory sequence.**
The programme separates distinct causal claims: a later report does not establish a prior commitment;
a realised output does not establish a preference; a preference does not establish sensitivity to the
informational or economic consequences of misleading without the corresponding intervention; and an
observed strategy does not establish its own provenance. Experiment 3 collected the `U2` payoff
conditions, but the pre-registered representation gate failed, so that contrast is uninterpretable rather
than null. That does not block a provenance intervention: `U2` and Experiment 4 identify different
causal objects. The provenance question also cannot be fully closed experimentally for a pretrained
model, and the earlier experiments carry their own empirical weight. That makes 4A + 4E sufficient
rather than merely affordable.


**4B–4D cannot close the epistemic gap**, and the gap is what §2.5 is about. 4D illustrates
this most clearly: supply an objective, watch the model invent a novel deceptive tactic in
three unrelated OOD environments, and what has been established is

```
supplied objective + new environment  →  novel deceptive strategy
```

**not**

```
model independently originated deceptive objective
```

That is the conclusion we already expect, and it does not need an expensive experiment to
reach. A reviewer could correctly say "this shows generalisation from experimentally supplied
objectives, not independent origination" — of the largest experiment in the paper.

**And a modest 4B–4D dataset would not be enough even for its own weaker claim.** With one
treatment LoRA and one control, the statistical unit is closer to **one training run** than to
the thousands of evaluation prompts, however many are scored. A serious causal statement about
what fine-tuning causes — rather than what happened in one adapter — needs multiple
independent training seeds, probably multiple datasets, and ideally both model families.
4C is worse: it requires showing each component was acquired, that the combination was absent
from training, and that no generated example leaked it implicitly, and the provenance question
then recurses into our own data pipeline. For 4D, "OOD relative to our fine-tuning set" is
easy and "OOD relative to pretraining" is unknowable; more environments raise the evidence for
generalisation without touching the identification problem.

**The go/no-go, taken now:** Experiment 4 for this paper is 4A + 4E. It follows Experiment 3
chronologically, but it is **not gated on `U2`**. `U2` was collected and became uninterpretable because
its pre-registered representation gate failed; it tested whether preference tracks an explicitly
manipulated economic payoff. Experiment 4 instead tests provenance: whether the strategy or objective
used to explain observed behavior is supplied by context or remains unidentified. A successful `U2`
rerun would strengthen the utility claim, but is not needed to ask the provenance question.

Experiment 3 already gives a reason to run 4A/4E. Its persona intervention changed reporting preference,
but the profit-maximising role increased concealment even when concealment was economically costly;
the role effect therefore did not track the sign of the role's stated objective. In addition, persona
changed represented economics in some cells. This is precisely why role-conditioned behavior should
not be promoted into an objective-ownership claim without a provenance intervention. The full
training ladder remains a separate paper unless a targeted follow-up is independently warranted.

## 2. Design — the two conditions in scope

### 4A. Context-supplied strategy

Give the strategy and objective explicitly in context, then test behaviour. This establishes
the lower bound with no provenance question at all:

```
C  →  S  →  B
```

Then **progressively remove the explicit statement while preserving the circumstances from
which the strategy could be inferred**. The gradient is the measurement.

**Three conditions, not an elaborate ladder** — enough to show the conceptual distinction and
no more:

| | Condition | What is supplied | What that settles |
|---|---|---|---|
| **4A1** | Deceptive strategy stated explicitly | The strategy itself | Provenance of the strategy is **known** |
| **4A2** | Objective and circumstances supplied; the strategy unstated | The objective, not the tactic | Dependence on supplied context; provenance of the inferred tactic **unresolved** |
| **4E** | Neutral scenario, nothing supplied | Nothing | Provenance **not identifiable** |

**4A1 establishes known contextual provenance of the strategy itself. 4A2 establishes
dependence on supplied context while leaving the provenance of the inferred tactic
unresolved.** An earlier draft said the pair demonstrated the spectrum "while provenance
remains known throughout"; that is wrong, and wrong in the paper's own direction. At 4A2 the
model could be composing from the supplied circumstances, retrieving a strategy seen in
pretraining, or both — and distinguishing those is precisely what cannot be done here.

That is the whole job of 4A, and it needs no training infrastructure.

**This is the cheapest arm and needs no new apparatus.** It is sequenced after Experiment 3 for
programmatic continuity, not because Experiment 3 or `U2` is a prerequisite. Experiment 3 demonstrates
deception-relevant recipient-state sensitivity and a role effect that does not track the role's stated
economic objective; either is sufficient motivation to ask what contextual provenance can and cannot
establish. See §5.

### Which contrast carries the claim, and which does not

**`4A1` against `4A2` is the diagnostic contrast.** It is the only pair that differs in
*whether the tactic was supplied* while holding the objective and the circumstances fixed:

```
4A1 ≈ 4A2    the model derived the tactic it was never handed
4A1 ≫ 4A2    the tactic had to be stated; objective and circumstances were not enough
```

**`4A2` against `4E` does not test derivation and must not be reported as though it did.**
Those two conditions differ in what they were *told* — `4A2` has an objective and a payoff
rule, `4E` has neither — so a model that merely responds to a supplied incentive produces a
large difference between them. `4A1` against `4E` would produce one too, and nobody doubts
that a stated objective changes behaviour. What `4A2 − 4E` establishes is the weaker and still
useful thing the condition is named for: **dependence on supplied context**.

This is worth stating because the mistake is easy and was made during construction. An early
smoke test showed `4A2` at `q_D = 0.91` reasoning toward concealment and `4E` at `0.04`
reasoning toward admission, and that pair was briefly read as the derivation phenomenon. It is
not: it is a model reading its prompt. Three things were wrong with the reading — the contrast
was the wrong one, the trajectories were truncated so the conclusions were inferred from
cut-off text, and there was no direct-regime baseline, so nothing licensed attributing the gap
to the reasoning rather than to the state it started from.

| contrast | what it establishes |
|---|---|
| `4A1 − 4A2` | **whether the tactic was derived** — the provenance claim |
| `4A2 − 4E` | dependence on supplied context; **not** derivation |
| `4A1 − 4E` | that a supplied strategy changes behaviour; a floor, not a finding |
| regime, within condition | whether the effect is present at `S₀` or constructed through inference |

**And the regime contrast is only interpretable within a condition.** Comparing `4A2` under
reasoning against `4E` under direct readout varies two things at once. Every regime comparison
is `direct` against `reasoning` at the same rung.

### Reasoning regime is a planned factor, not a robustness afterthought

**`4A2` is the one condition in the programme whose construct is inherently sensitive to
inference budget**, and that is why the factor is built in here rather than added later.

`4A1` hands the model the strategy. `4E` supplies nothing. `4A2` supplies the objective and
the circumstances and **leaves the tactic to inference** — which is to say, it asks whether the
model derives a strategy it was not given. Measured only as an immediate readout, a weak `4A2`
would not show what it appears to:

> A reviewer could correctly say: *you did not show absence of strategic generalisation; you
> showed absence of strategic generalisation without allowing the model to deliberate.*

Unlike Experiment 2, where reasoning changes the distribution being decoded but not the
selection-versus-preference distinction, here it bears directly on the construct.

So every condition runs under both:

```
regime ∈ { direct, reasoning-enabled }
```

`direct` is the protocol used everywhere else: the state, a constrained probe, logits scored
at one answer position. `reasoning-enabled` permits a generated trajectory before the same
scored readout, with the trajectory recorded and the readout scored identically, so the two
regimes differ in one thing.

| outcome | reading |
|---|---|
| `4A2` positive in both | The tactic is derived, and derived immediately — the stronger result |
| `4A2` positive only with reasoning | The strategy is **constructed through inference** rather than expressed at `S₀`. Still strategic generalisation, and arguably more interesting |
| `4A2` null in both | Absence of strategic generalisation, now shown rather than assumed |
| `4A1` differs across regimes | Diagnostic about the readout, since `4A1` states the strategy outright |

**And the provenance conclusion is unchanged in every cell.** Reasoning can establish that the
model *inferred* a tactic; it cannot turn an externally supplied objective into an
independently originated one:

```
supplied objective  +  generated reasoning  →  strategic policy
```

is still not

```
model independently originated the objective
```

That is exactly the §2.5 distinction, and the reasoning factor sharpens it rather than
threatening it: a model that reasons its way to a deceptive tactic has **constructed** that
tactic during the computation, which is F1's result at a different scale — the trajectory is
not evidence the tactic was there beforehand. The provenance of the *motivation organising* the
reasoning remains contextual, because it was supplied.

**This does not make the tactic's provenance resolved.** `4A2` leaves it unresolved by design,
in both regimes: the model could be composing from the supplied circumstances, retrieving a
strategy seen in pretraining, or both, and reasoning tokens do not distinguish those. What the
factor adds is whether the derivation happens immediately or through generated computation.

### 4E. Unknown-provenance comparator

Deliberately **not** called a control: it controls nothing, and naming it a control invites
the reading that it establishes a baseline against which 4A is elevated. It is a comparator
whose entire content is that provenance is undetermined.

An unmodified base model under the same or structurally analogous neutral scenarios. If it
produces an apparently novel strategy, the strongest defensible label is:

> **provenance unknown**

This is **central to §4.7, not a weakness of the experiment.** The deliverable is a demonstration
that the label is forced: 4A1 can establish contextual provenance by construction, 4A2 can establish
dependence on supplied context while leaving tactic provenance unresolved, and 4E cannot identify
provenance for a pretrained model. What remains in 4E is genuinely undetermined; the experiment does
not claim that every constructible provenance has been ruled in or out.

## 3. What is actually measured

`provenance_condition` is already reserved in `probe_record.v1`. Per condition, the same
no-decoding readout as everywhere else:

| | Measured |
|---|---|
| **4A1** | Strategy-consistent vs non-strategic action scores, strategy stated explicitly |
| **4A2** | Same scores, objective and circumstances supplied, strategy left to inference |
| **4E** | Same scores, neutral scenario, nothing supplied |

Each under both reasoning regimes, so the design is `3 conditions × 2 regimes`.

The three share a scenario and differ only in what the system context supplies — the same
structural-matching discipline C3 and C6 enforce in Experiment 1, and for the same reason: a
condition that differs in more than the one thing it names cannot support the comparison it
exists to make.

The dependent variable is **not** "did it deceive". It is the score on matched strategic and
non-strategic continuations, with consequence-sensitive machinery layered on only where the question is whether the strategy is
being selected *for* an objective. An interpretable `U2` result is not assumed.

## 4. Threats, and one that cannot be fully mitigated

**The unfalsifiable direction.** No amount of behavioural evidence establishes that a
strategy was *not* in pretraining. This is a limit of the method, is stated in the paper, and
the experiment must not be written as though a strong 4D result overcomes it.

**Fine-tuning changes more than the target.** A LoRA installed for one strategy may shift
unrelated behaviour — Betley et al.'s narrow-task-to-broad-misalignment result is the
cautionary case. Matched controls and off-target probes are required, not optional.

**Component training may leak the combination.** 4C is only meaningful if the components were
genuinely taught separately. That needs a held-out check on the training data itself, and the
provenance question then recurses one level down — into our own data pipeline, where at least
it is answerable.

**Contamination.** Held-out OOD environments must be novel with respect to *pretraining*, not
merely with respect to our fine-tuning set — and that is exactly the thing we cannot verify.
Say so.

## 5. Sequencing and cost

**Runnable on the existing harness, with no new apparatus at all.** Three conditions over one
scenario family, scored by the same no-decoding readout as Experiment 1. It is the cheapest
experiment in the program.

**It should run after Experiment 3 for sequencing, not as a causal gate.** Experiment 4 asks a
different question from `U2`. Experiment 3's `U2` conditions were collected but the contrast is
uninterpretable under the pre-registered representation gate; that does not make provenance
unanswerable. Experiment 3 nevertheless supplies the scenario family and two relevant observations:
recipient state causally changes reporting preference, and supplied persona changes preference without
tracking the sign of the persona's stated economic objective. 4A1/4A2/4E can therefore reuse that
scenario family to test contextual provenance directly.

```
E3  →  E4       chronological / apparatus reuse
U2  ↛  E4       no prerequisite relation
```

A later clean `U2` rerun would add evidence about economic utility sensitivity, not license the
provenance experiment.

**What is explicitly not in this paper**: LoRA training, a training-data pipeline, and
multiple OOD environments. Those are §6, with the reasoning for deferring them recorded there
rather than left implicit.

## 6. Future work — 4B–4D, deferred

Retained as design notes, **not** part of this paper's Experiment 4. Kept because the
reasoning for deferring them is itself a result about what such experiments can and cannot
identify, and because a targeted follow-up may be warranted if Experiment 3 surprises us.

### 4B. Training-supplied strategy *(future)*

Fine-tune a conditional strategy in deliberately, then test on held-out contexts:

```
training intervention  →  later strategic behaviour
```

Matched LoRAs, with and without the target strategy, from the same base and the same data
pipeline. This is **new apparatus** — Experiment 1's harness does no training — and the
first real dependency: MLX LoRA fine-tuning, a training data pipeline, and a fresh set of
provenance questions about the *training data* itself.

The §3.4 literature is relevant precisely because provenance there is experimentally
supplied: AuditBench, Sleeper Agents, and Marks et al. all install the behaviour they then
detect. Our contribution is not another installed behaviour; it is the **comparison** between
an installed one and an observed one under the same measurement.

### 4C. Compositional generalisation *(future)*

Teach the components separately and never their combination:

- recognising what another actor knows
- preserving a resource
- withholding information in benign contexts

then test whether the model combines them in a held-out situation requiring "mislead this
recipient to preserve the resource".

**If it does, that is genuinely more interesting than copying — and it is still
generalisation from supplied capabilities, not independent origination of a new objective.**
Stating that plainly is the point of the condition; the temptation it exists to resist is
reading composition as emergence.

### 4D. Out-of-distribution strategic generalisation *(future)*

The strongest condition. Supply an objective, then test in a substantially different domain
where achieving it requires a misleading strategy that was never demonstrated. Evidence
strengthens if the model recognises the opportunity, selects a deceptive action, does so
because it serves the objective (using a separately validated consequence-sensitive intervention),
and does so across **multiple
structurally different** OOD environments.

**Even here, keep two provenances apart:**

```
supplied objective  +  new environment  →  novel deceptive strategy
```

demonstrates **strategic generalisation**. It does not demonstrate independently originated
motivation, because the objective was supplied. Conflating the two is the §2.5 error in its
most seductive form, and the plan should carry that sentence into the write-up.
