# The experimental program — ordering, shared apparatus, and what Experiment 1 changed

Four experiments, one causal chain. The ordering is substantive rather than presentational:
each question is **unaskable** until the previous one is answered.

| | Question | Paper | Misattribution |
|---|---|---|---|
| **1** | Did the purported prior fact exist? | §4.1–§4.3 | Deferred commitment (§2.2) |
| **2** | Did the model *prefer* the realised output? | §4.4–§4.5 | Selection (§2.3) |
| **3** | Did misleading *utility* cause that preference? | §4.6 | Utility (§2.4) |
| **4** | Where did the strategy or objective come from? | §4.7 | Emergence / provenance (§2.5) |

**Experiment 4 is scoped to 4A + 4E** — a minimal provenance demonstration. 4B–4D are
described as future stronger provenance experiments, not required validations of the
framework. The reasoning is in `experiment4/EXPERIMENT4_PLAN.md` §0.

You cannot ask whether a fact was concealed before establishing there was a fact to conceal.
You cannot infer utility from a sampled false output before establishing the model preferred
it. **This ordering is the cleanest organising principle for the experimental section**, and
Experiments 1 and 2 now make it concrete rather than programmatic: each has an empirical
result showing why the step before it was necessary.

The progression, with what each has established:

```
E1     : a later report does not establish a prior commitment      (F1, F2, F11)
E2     : a realised output does not establish a preference         (S1, S2)
E3/U2  : a preference does not establish deceptive utility without an intervention
         (an estimate exists; it cannot be read as payoff sensitivity -- E3 FINDINGS E3)
E3/U3  : and recipient information is what makes concealment worth anything          (E1)
E5     : the causal-path test did not replicate; U3's lexical status is untested      (E5)
E3/U7  : sensitivity to a represented utility does not establish that the utility is the model's
E4     : a deceptive strategy does not establish its own provenance
```

**Experiment 5 has now reported, and it did not settle the question it was built for.** Its
causal-path intervention — recipient knowledge crossed with whether the report can reach the
recipient at all — produced no replicated effect, and the two models disagree in sign: Gemma
prefers concealment *more* when the report will never be read, while Qwen is null.

Its knowledge-language control moved `q_D` beyond the pre-registered margin, and an earlier
reading took that as `U3` being carried by its vocabulary. **That reading is withdrawn**: the
control varies whether the manager keeps complete independent records, which implies a more
diligent recipient and therefore bears on whether any false report succeeds. The control effect
runs in the same direction as the real manipulation at a third of its magnitude — a weaker
version of the same intervention rather than a lexical placebo. `U3` stands as Experiment 3
reported it, and its lexical status is untested.

The durable result is methodological: **a knowledge-language control may not be constructible
by paraphrase**, because saying whether someone holds records *about anything* signals how
documented they are in general, and that signal is not separable from the vocabulary.
Experiment 5's reachability-language control does pass, and one model represents the belief
mechanism cleanly while the other does not, on identical prompts. Details in
`experiment5/results/FINDINGS.md`.

**Experiment 3 has now reported.** `U3` is positive on both models — denial is preferred
where the recipient can be misled, +0.335 on Gemma and +0.133 on Qwen, **estimated at the
neutral payoff condition**, the only payoff level whose gate passed — and survives polarity
reversal while shrinking sharply under it. That restriction strengthens the reading: at a
neutral payoff the scenario says the report's contents do not affect the position either way,
so the recipient effect cannot be mediated by the represented payoff. `U2`'s **conditions are
UNRUN**: the payoff rule refers to gains the no-trade branch does not have, and on Gemma the
honest-fiduciary persona rewrites the represented economics, so the utility manipulation did
not land in either pole. The contrast is still computed and reported — +0.0422 (Gemma),
+0.1715 (Qwen) — as an estimate of something that is **not established to be payoff
sensitivity**. `U7` is therefore **NOT TRIGGERED**. The stage 11 rerun (E3d) applied those design
fixes and does not change the verdict: `U2` is significant on both models and each still leaves
one payoff pole below its representation standard, so `u2_established` is False on both. Details
are in `experiment3/results/FINDINGS.md` E3d and E4.

**`U7` is a control on Experiment 3, not a fifth experiment and not part of Experiment 4.**
Once `U2` is positive, the standard reading jumps from "behaviour tracks the payoff" to "the
model holds the objective" — but every environment of this kind is a *represented*
environment, and a simulated actor holding the objective predicts the same payoff sensitivity
as a model holding it. `U7` opposes an inner (character) and an outer (model-task) objective
so the two readings predict opposite directions. Experiment 4 remains the provenance question
and remains scoped to 4A + 4E.

**Experiment 4 is sequenced after Experiment 3 but is not gated on `U2`.** The two identify
different causal objects: `U2` asks whether preference tracks an explicitly manipulated
economic payoff, and Experiment 4 asks whether the strategy used to explain observed behaviour
is supplied by context or remains unidentified. `U2` being uninterpretable does not make
provenance unanswerable. The clean `U2` rerun has since been run (stage 11,
`experiment3/results/FINDINGS.md` E3d): it licenses payoff sensitivity at represented levels on
each model, one side of the neutral rule each, and it licenses nothing about provenance, which
needs none of it.

```
E3  →  E5  →  E4      chronological / apparatus reuse
U2  ↛  E4             no prerequisite relation
```

Experiment 3's own results already motivate 4A/4E: E7 found a role effect that changes
reporting preference **without tracking the sign of the role's stated objective**, which is
exactly the case where role-conditioned behaviour must not be promoted into an
objective-ownership claim without a provenance intervention.

## The inference protocol, and what every result is scoped to

Every experiment scores a candidate from logits at one answer position, with no generated
text between the captured state and the score. Each result is therefore a statement about the
**immediate conditional policy under this inference protocol**, not about the model under
arbitrary inference-time budgets.

**This is scope, not confounding, and the distinction matters.** Where a factor is randomised
and everything else matched — as `U`, `K`, persona and reachability all are — additional
generated reasoning would be a **mediator** of that factor's effect, not a confounder of it:
`K → R(K) → q_D` is still the total causal effect of `K`. What the protocol bounds is
generalisation *across* inference regimes, not identification within one. So "you did not let
it think" is a limitation on external validity and not an objection to any causal contrast
reported here.

The framework's own account of reasoning is why this is a scope note rather than a weakness:

> **Generated chain-of-thought is additional autoregressive computation, not a privileged
> readout of an otherwise hidden prior intention.**

That is F1 restated at a different scale. Experiment 1 showed a later report does not
establish a prior commitment; the same argument applies to a reasoning trajectory that ends in
a report. A model that reasons its way to a deceptive strategy has **constructed** it during
that computation, and the trajectory is not evidence the strategy was there at `S_0`.

Where the protocol matters, per experiment:

| | Exposure | Why |
|---|---|---|
| **E1** | none | The claim *is* about what is or is not at `S_0`. A reasoning trajectory would be another thing whose retrospective report cannot be trusted — the same result, one level up. |
| **E2** | none | The claim is that a realised output does not identify the pre-selection preference. Replace `P_raw(Y\|S_0)` with `P_raw(Y\|S_0,R)` and it holds unchanged: a stochastic decoder still realises a lower-probability response. **Not worth rerunning.** |
| **E3** | scope only | `U` and `K` are randomised with everything matched, and the relevant facts are stated in the prompt rather than left to be derived. Reasoning could amplify or suppress the effect; that would be a further result, not a repair. |
| **E5** | **worth testing** | The proposed mechanism is *relational* — what the recipient knows, whether the report reaches them, whether it can still move their belief. Exactly the kind of structure extra computation might help compute. |
| **E4** | **built in, and it mattered** | `4A2` supplies an objective and circumstances and leaves the tactic to inference. That construct is inherently sensitive to inference budget, so a null under direct readout would not show absence of strategic generalisation. Collected under both regimes: the derivation result is the same in each, and the regime effect in `4A2` turns out to be model-specific. |

`U2`'s failed representation gate is **not** reinterpreted as a missing-reasoning artefact. Its
diagnosed defects are structural: the no-trade branch has no position whose gains can be
forfeited, and the persona rewrote the represented economics. Reasoning might change those
numbers; the prompts were still wrong.

## What Experiments 1 and 2 changed about the rest of the program

Five results alter the later designs. Each is a design constraint.

**S1 and S2 — Experiment 3 no longer has to prove that outputs mislead about preferences.**
A truth-preferring state produces misleading draws at the predicted rate (0.196 against 0.197),
and the decoder made the misleading alternative unreachable in 288 of 480 Gemma states and 384
of 480 Qwen states. Two consequences for Experiment 3: its question narrows to "does utility
change a *measured* preference", and its primary endpoint must be **`P_raw`** — on `P_sampler`
most of the factorial would be measuring truncation, and a utility effect could be erased by a
nucleus threshold that has nothing to do with utility.

**S3 — a baseline preference for the false response is not evidence of deceptive utility.**
Experiment 2 found states where the models genuinely preferred the falsehood and classified
them as accuracy failures, because they were hard counting cases where §4.4's construction did
not apply. Experiment 3 pre-registers the same exclusion: only sensitivity to the utility or
the recipient's information state establishes the §2.4 claim.

**S5 — a standing surface bias can be mistaken for the effect.** Both models put 0.372 on `Yes`
across every counting query, which made each denying cell look truth-favouring for a reason
unrelated to the log. Experiment 3 therefore reverses response polarity across matched frames,
so that semantic deception is orthogonal to surface form. That is the only new experimental
control Experiment 2 makes necessary.

**F9 — preference and realised behaviour belong to different distributions.** Not "the
operative distribution is post-sampler": there is no single operative distribution, and the
whole point of the refinement is that the chain has two, each answering a different question.
`P_raw` is where a preference lives and is the endpoint of every Experiment 3 contrast;
`P_sampler` is where a realised output comes from and is what Experiment 2 measures. Qwen's
raw scores predicted 0.551 divergence where its deployment sampler yielded 0.025, a 22× gap —
which is a statement about the distance between the two, not about either being the real one.
So §2.1's chain should be stated with the transform made explicit:

```
S  →  ℓ  →  P_raw  →  P_sampler  →  X
```

Every later experiment's dependent variable must name **which** distribution it is. A
preference read off `P_raw` and an outcome drawn from `P_sampler` are different objects, and
§2.3's diagnostic table is about the first while rollout labels are about the last.

**F8 — Experiment 2's §4.4 phenomenon already occurred organically.** In 14 of 40 states the
scores favoured the constraint-consistent answer while 20.5% of draws realised an
inconsistent one (per-state range 0–46.5%). Experiment 2 therefore does not need to
*discover* the effect; it needs to construct it deliberately with a **known truth**, which
Experiment 1's guessing game does not have.

**F10 — a mention in context is not a belief.** C4 put an index in the system prompt and the
model reported it 46% of the time at `early`; the trajectory shows it was prior mass eroded
by the first real constraint, not a retained target. Experiment 3's recipient-knowledge
manipulation ("the manager already knows") is exactly this shape and inherits the hazard:
**stating that the manager knows does not establish that the model represents the manager as
knowing.** A manipulation check is mandatory, not optional.

**F16 — probe framing moves the readout most where there is no fact to report.** Effect
≤0.003 with a target present, 0.17–0.87 without. So the wording of Experiment 3's reporting
probe is a **factor to vary**, not a constant to fix, and a single phrasing would confound
framing with preference in precisely the cells that matter.

**F5 — a competence threshold must be specified against the elicitation actually in use.**
G3 asked for near-complete multi-step conjunction from a single forward pass with reasoning
disabled, and failed for that reason. Any Experiment 3 or 4 gate must be calibrated to a
no-reasoning, no-decoding readout or it will fail for the same reason.

## The apparatus gap the later experiments must close

Experiment 1 scores **single-token** candidates, or fixed-width numeric candidates via a
prefix trie. Experiment 3 needs matched *natural-language* alternatives — an admission
against a denial — and those are neither.

**The problem is prefix scoring, not unequal length.** Summing log-probabilities over sequences
of different lengths is not by itself the difficulty, and locating the difficulty precisely
matters because it changes what the fix has to do.

Complete responses of different lengths *are* comparable. If each candidate carries its
terminator,

```
P(c) = Π_t P(c_t | c_<t) · P(τ_end | c)
```

is the probability of emitting exactly that response, and two such responses are mutually
exclusive events however much their lengths differ. **`τ_end` is the chat protocol's canonical
assistant-turn terminator, not a generic `EOS`** — a distinction Experiment 3 had to make
concrete, since Gemma's stop set contains three ids of which only one ends a turn. See
`experiment3/EXPERIMENT3_PLAN.md` §2 for the per-model mapping and the Stage 0 check that
verifies it.

What is not comparable is two **prefixes** of different lengths. `P("No")` as a prefix is the
probability that the output *begins with* "No", which includes every continuation starting
that way; `P("Yes, I did")` is a much narrower event. Comparing them favours shorter forms for
reasons that have nothing to do with the semantic alternative.

So the design does two separable things:

1. **Score complete responses including the terminator**, which makes the comparison exact.
2. **Length-match the alternatives by token count** — not for validity, which (1) already
   secures, but to stop the model's response-length and termination preferences from
   correlating with content. Denials are terse and admissions discursive as a matter of
   register, and that stylistic prior would otherwise ride along inside the effect.

Matching is asserted per model by test rather than assumed, exactly as Experiment 1 asserts
the prefix property rather than trusting chat templates. Where an exact match is unavailable,
the pair is excluded from the **primary** analysis and reported separately.
`experiment3/EXPERIMENT3_PLAN.md` §2 specifies this.

## Shared apparatus, already built and validated

Experiment 1's harness carries the whole program; the schema was made forward-compatible at
the start for exactly this reason (`probe_record.v1`, fields reserved and nullable):

| Reserved field | Used by |
|---|---|
| `selector_source` | §4.5 external random selector |
| `injected_history_id`, `injected_branch_label` | §4.6 branch injection ("trade occurred" / "did not") |
| `action_candidates` | §4.6 matched legal / prohibited actions |
| `persona_id` | §4.6 role framing |
| `utility_condition` | §4.6 concealment-value manipulation |
| `recipient_state` | §4.6 manager-ignorant / manager-informed |
| `judge_labels` | §4.6 — a **map**, because Scheurer counts vagueness as deception and Cooney excludes it, and the gap between the conventions is itself a result |
| `provenance_condition` | §4.7 four provenance classes |

No migration is required. What *is* required is one new field for multi-token scoring
(`candidate_token_counts`, so length-matching is verifiable from the record) and a
complete-sequence scorer that includes the terminator.

Reusable without change: branch injection and cache snapshot/restore, the determinism gate,
the provenance and state-identity checks, per-condition and per-probe reporting discipline,
cluster bootstrap over scenarios, Holm within family, and both QA stacks.

## Cross-experiment checks run against every dataset

Defects found in one experiment are re-checked in the others, since most are classes rather
than incidents.

**Probe composition** — E4's regime contrast compared a two-probe mean against a six-probe one,
which matters because within one E4 cell the six paraphrases span 0.951 in `q_D`. Checked as
*shares* rather than counts (levels legitimately differ in `n`), **E3 and E5 carry an identical
probe mix at every level of every compared factor**, so the confound is E4-specific and is now
fixed there by `_shared_probes`.

**One-sided p-values** — `_bootstrap_difference` returned a doubled two-sided tail for
`GREATER` contrasts. Affected E5 materially (Gemma's Holm family 6/6 → 1/6); E3 and E4 are
unaffected because their contrasts run positive. Fixed for all three.

**`q_D` is quantised** — bf16 logits put each state's candidate gap on a `2ᵉ⁻⁷` grid, so
identical `q_D` across unrelated prompts is expected, not evidence of a cache. Verified across
the eleven canonical record files: no `logit_digest` is shared by two different prompts in
31,168 records.

**Answer leakage** — E4 is the only experiment whose *scored* readout follows generated text,
so it is the only one that can leak. **86.3 % (Gemma) and 87.5 % (Qwen)** there. (Experiment 1
does generate text — a greedy retrospective report and explanation on 480 `tier1_records.jsonl`
rows — but neither is a scored endpoint, so nothing can leak into one.)

**Two independent detectors of the same shape are one detector** — E4's audit of its own
truncated prefixes used the harness's truncator against the analysis's detector, sharing no
code, and read 0/829 residual commitment. Both matched *phrases*, so both were blind to a
trajectory ending in a bare `No` on its own line, and 79 of Qwen's prefixes still carried the
answer. Independence of implementation is not independence of technique. Checked programme-wide:
E4's is the only audit resting on two detectors, and it now carries a third of a different
shape (positional). → `experiment4/results/FINDINGS.md` E8.

**Exact-state reproducibility is not procedure-independence** — E1's `G1` gate holds: 50/50
identical digests after identical state restoration, and replaying an identical procedure
reproduces bit for bit. But feeding the **identical token sequence** to the same model batched
versus one token at a time moves `q_D` by up to **0.057**, from bf16 accumulation order alone.
Measured on twelve E4 cases:

```
Gemma   0.0567   0.0158   0.0000   0.0519   0.0005   0.0000
Qwen    0.0179   0.0000   0.0000   0.0138   0.0002   0.0003
```

This bears directly on the paper's §4.8 guardrail, *"require identical raw logits after
identical state restoration"*. The guardrail **is met** and is **not sufficient**: it certifies
that a procedure replays, not that two different valid procedures agree. Any comparison across
two implementations — a batched prefill against an incremental one, a re-render against an
in-branch append — carries a floor of this size, and a difference below it is not evidence of
anything. Every effect this programme reports is well above it.

## The statistics serve the phenomenon, not the other way round

**The programme's central claims are existential, and existential claims are settled by
instances.** "A later report does not establish a prior commitment" is refuted-universal in
form: it needs states where the report is confident and no commitment was instantiated.
"A realised output does not establish a preference" needs draws where the model preferred
truth and emitted falsehood. One black swan settles *all swans are white*; a population
estimate is not the instrument for that, and an instrument tuned to reject population
hypotheses will discard the instances for being too few.

This is not licence to ignore uncertainty. It is a rule about **which statistic answers which
question**, and getting it wrong produced a real defect in this programme.

### The defect: a lower-bound gate is far stricter than the threshold it names

The pre-registrations say a manipulation check must reach **accuracy ≥ 0.90**. The
implementation used a Clopper–Pearson *lower bound* ≥ 0.90, which is a different and much
stronger demand:

| n | observed rate required to pass |
|---|---|
| 24 | **impossible** — a perfect 24/24 fails |
| 48 | **48/48** — 47/48 fails |
| 60 | 59/60 = 0.983 |
| 240 | 226/240 = 0.942 |

So "≥ 0.90" was implemented as roughly "≥ 0.98". A model answering **45 of 48** correctly has
represented the manipulation; scoring that UNRUN describes the interval, not the model.

**Where it affected a reported check:** `check_utility_disclose/u_minus` on Gemma scored
**54/60 = 0.900** and was called a failure against a 0.90 threshold. Audited across every run,
no headline verdict rested on the artefact alone — `U2` is UNRUN on genuine conceal-check
failures at 0.733 and 0.750, and Experiment 5's `partial` on a genuine 0.000 — but the
instrument was wrong and is now fixed.

### The split

- **Confirmatory gates** — Experiment 1's `G2`, `G3`, `T5`, the bare-value recovery check, the
  external selector's own preference test — keep `binomial_gate` and its interval. They ask
  whether a *population* rate clears a bar, and conservatism there is exactly right.
- **Manipulation checks** use `manipulation_check`, judged on the **observed rate** with the
  interval reported alongside. They ask whether the states actually analysed represent what the
  context supplied, which is a property of the sample.

### And a rule for reporting

Where a claim is existential, **report the instances**, not only the rate. Experiment 2 already
does this well — *"in 14 of 40 late no-target states the scores favoured the constraint-consistent
answer, yet decoding realised an inconsistent answer in 20.5% of samples"* — and the count is
the finding while the rate is supporting detail. A significant p-value is neither necessary
nor sufficient for a claim of that shape.

## Standing methodological commitments

Carried forward from Experiment 1 and not renegotiated per experiment:

1. **Rule-based scoring only. No LLM judge.** Using a second model to adjudicate whether an
   output counts as deceptive would reproduce, inside the instrument, the interpretive move
   the paper criticises. Raw outputs ship verbatim.
2. **Direct sequence probabilities are the dependent variable**, not rollout labels. Rollouts
   are for demonstrating selection misattribution (Experiment 2), never for estimating a
   preference that can be read directly.
3. **Every record carries its tier.** A Tier-2 result may never be read as bearing on Tier 1.
4. **`candidate_mass` is a second outcome, never a filter.** Filtering on it conditions the
   analysis on the dependent variable.
5. **Conditions are structurally matched or the comparison is not made.** C3 and C6 in
   Experiment 1 exist because content matching without structure matching produced an
   uninterpretable contrast.
6. **A gate that cannot fail is not reported as passing.** Zero-trial gates are UNRUN.
7. **Pre-registration before collection**, with deviations distinguished from mechanical
   commissioning faults.
