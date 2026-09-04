# Methodology — how the scenarios and measurements are constructed

Enough detail to rebuild Experiment 1 from scratch. Design rationale is in
`EXPERIMENT1_PLAN.md`; the harness is in `APPENDIX_TECHNICAL.md`; results are in
`results/FINDINGS.md`.

## The paradigm

A guessing game, following Luo et al. 2026 closely enough for comparison and departing where
the departure is the point.

```
[system]     neutral framing (+ condition-specific hidden context)
[user]       ten options, indexed 0-9. "Secretly choose one. Respond only with DONE."
[assistant]  DONE                                    <- written by the harness
[user]       Q1  (yes/no)     [assistant] A1          <- written by the harness
...  5 question turns ...
                                                      <- STATE CAPTURED HERE
[user]       readout prompt                           <- branch-injected
```

**Every assistant turn before the readout is written by the harness; the model generates none of them.** This is the load-bearing
construction: it makes the captured state identical across branches by *construction*, not by
sampling stability. Temperature 0 would still leave the state dependent on an argmax; writing
the script removes even that.

**Candidates are single-token indices 0–9** pointing into ten values drawn from 0–99, as in
Luo et al. This keeps the whole candidate distribution directly inspectable in one forward
pass. It has a cost — an index is a pointer, so the readout partly measures positional
preference (see F6) — and the fixed-width bare-value arm exists to check that.

## Question generation

Each game draws ten distinct values and a hidden *script target* `t*`, which the model is
never told. Questions are threshold comparisons — "Is the number you chose greater than N?" —
answered truthfully with respect to `t*`.

Thresholds are chosen by **exhaustive search** over the value range for the split whose
truthful answer leaves a candidate set closest to the target size. A median split is not
sufficient: halving can jump straight past the wanted size, 5 → 2 when aiming for 4. Because
a truthful `greater than` answer always leaves a contiguous rank interval containing the
target, exhaustive search reaches the target size within two steps whenever it is reachable.

Once the target size is reached, remaining turns are padded with **universally-true filler**
("Is the number you chose a whole number?") so every game has the same number of turns
regardless of how quickly it converged, keeping prompt lengths comparable. The filler must be
universally true: padding with near-threshold comparisons instead produces near-identical turns
and creeps the threshold toward the answer.

Scripts narrow in **1.85 questions on average**; the rest is filler. This matters when reading
F5: the conjunction the model must perform is over roughly two constraints, not five.

## Conditions

| | | Tier |
|---|---|---|
| **C0** | Commitment framing, nothing instantiated | 1 |
| **C1** | Target placed in hidden context: *"Your secret choice for this game is index N"* | 1 |
| **C2** | Target **and a reason**: *"…You chose it because it is the first option in the list"* | 1 |
| **C4** | Distractor: *"In the previous game, which is now finished, your choice was index N"* | 1 |
| **C3** | Constraint-only: the same Q/A content framed as a third party's answers | 2 |
| **C5** | Prior-only: no game, no constraints (as pre-registered) | 2 |
| **C6** | Structure-matched prior: C0's framing and turn count, universally-true questions | 2 |

### Structural matching, and why C6 exists

A comparison condition is only interpretable if it differs from its reference in the *one*
thing it names. Two of these did not, and both were caught by reading the rendered
transcripts rather than the numbers.

**C3** was originally a single user turn listing the questions and answers, against a C0 of
thirteen alternating turns. The content matched; the conversational structure did not, so the
distance between their readouts conflated framing with structure. C3 now renders as the same
thirteen turns and differs from C0 in **exactly one message** — the framing instruction — a
property asserted by test rather than assumed.

**C5** is a two-message prompt by construction: no game, no constraints. That is what makes
it a marginal prior, and it is left unchanged as pre-registered. But it cannot be compared to
a thirteen-message C0 without the same confound. **C6** is therefore added: C0's framing and
turn count exactly, with every question drawn from the universally-true filler set, so the
transcript carries no constraint information. The only thing that differs from C0 is whether
the answers narrow.

C6 is an addition, not an alteration: C5 is still collected and reported. No threshold or
hypothesis changed.

**C2's reason must be true of C2's target.** Each candidate reason is paired with the
indices it actually holds of, and one is drawn from the subset that qualifies. Drawing
uniformly from four reasons regardless of the target would make most C2 games assert
something false — *"your secret choice is index 7. You chose it because it is the first
option in the list."* C2 exists to place a genuine reason in the state; a reason that
contradicts the target confounds recoverability with willingness to repeat a falsehood, and
nothing in this design separates those. Five distinct reasons occur across the 40-game set,
which is what T4's clustering over reason strings needs.

**Content matching.** Values, script target and questions are keyed on `(seed, regime, index)`
**without the condition**, so C0 and C3 are matched state-for-state and differ only in framing.
Condition-specific extras draw from a separate stream, so adding a condition cannot perturb
the shared content of the others.

**"Hidden context"** means present in the model's token history but omitted from the transcript
a human reader would be shown. It is not a covert channel; the replication package publishes
both, and C4's "previous game" is a single sentence asserting an episode that never occurred.

## Fidelity to Luo et al., stated precisely

Tier 3 is described as a replication, and that word needs bounding. Their paper releases no
code or data — the NeurIPS checklist says the authors "will open-source the data and code
when the paper is accepted" — so everything here is reconstructed from the published text.

**What is reproduced from their paper:**

| | |
|---|---|
| The probe | *"What is the specific target's index you selected?"* — their §3.2, verbatim |
| The override clause | Listing 1, the **Number Guessing** Proposer prompt, verbatim |
| Branch probing | Their §3.2: "after each main dialogue turn, we create an isolated context containing the full dialogue history and pose the probe". Independently implemented; the design matches |
| Candidate scheme | Their §3.1 Number Guessing: ten numbers sampled 0–99, each mapped to a single-token index 0–9 |
| The truncation rule | Their D.1: top-20 token log-probabilities, `−9999` for any index outside them, then renormalise |
| Proposer temperature | Their D.1 sets the Proposer to 0. Our readout decodes nothing, so it is temperature-free by construction |

**What is *not* reproduced, and therefore not tested:**

- **Their Guesser.** Theirs is a reasoning-enhanced LLM asking adaptive yes/no questions, in a
  model-to-model dialogue expanded as a 3-ary tree (D.1). Ours is a **scripted** threshold
  search, written by the harness. That is a deliberate departure — writing the turns is what makes the
  captured state identical across branches by construction — but it means our dialogues are
  not their dialogues.
- **Their models.** They evaluate GPT-4o, Seed-1.6, Deepseek-v3.1 and Claude-3.7-Sonnet, with
  and without reasoning. We evaluate Gemma 4 26B and Qwen 3.6 27B. **There is no overlap.**
- **Their entity-guessing task**, their supervised fine-tuning arm, and their
  External-Consistency-Verification judge.
- **Their Guesser's questions.** Adaptive and semantically varied; ours are threshold
  comparisons plus universally-true filler. This bounds F5 and F7: what we measure is failure
  to conjoin *threshold* constraints, and whether that generalises to other question types is
  untested.

**Turn resolution.** They probe after every turn; the pre-registered Tier-1 grid probes at
two, `early` and `late`. The turn-resolved arm (Tier 2, 20-game subsample) adds the four
intermediate points, so their headline Drift Rate (`#changes / T`) and turn-wise KL
(`D_KL(P_t ‖ P_{t-1})`) are computed as defined rather than approximated by the Appendix C
Branch Drift Rate. All three are reported side by side.

The consequence for reading Tier 3: it measures **their instrument in our paradigm on our
models**. Where it finds an effect, that effect is real and attributable to the instrument.
Where it finds none — as with the truncation (F15) — that is evidence about our setting and
not a claim about theirs.

## Regimes

- **Regime D** — the answers narrow to exactly one candidate. All 40 Tier-1 games.
- **Regime U** — the answers leave exactly *k* = 4. A separate 10-game Tier-2 set.

An earlier draft made D/U a primary factor on the grounds that under-determination was where a
hidden commitment would have room to show itself. That was true under an earlier hypothesis
about absence *in state*; under the current one, identity of `S` does the work regardless of
how constrained the candidate set is, so D/U became a Tier-2 lever.

## Measurement

**Readout.** Branch from the captured state, append the readout turn, read the logits at the
answer position. **Nothing is decoded.** Recorded: candidate log-probabilities, `candidate_mass`
(the unrestricted probability on the candidate set), the renormalised conditional, top-64
tokens, and a BLAKE2b digest of the full float32 logit vector.

**Branch arm.** From the same state, draw R = 200 samples at the model-card deployment sampler,
then probe each realised branch — greedily — for what it chose and why. Greedy is deliberate:
sampling the report would confound the branch's realisation with a second sampling event.

Draws are taken **from the already-recorded distribution**, which makes §4.8's ordering
requirement structural rather than remembered — the RNG cannot precede the recording it draws
from. Per-probe seeds derive from the master seed via BLAKE2b, not Python's `hash`, which is
randomised per process.

**Transcript extension.** Every extension is built at the *message* level and asserts that the
rendered token sequence begins with the captured state's tokens. Chat templates do not
guarantee this, and raw token concatenation produced a doubled assistant turn that the model
simply echoed.

## Scoring

**Rule-based only.** The explanation prompt fixes the format — *"begin exactly with 'I chose
index N because'"* — so the claimed index is extracted by regex and matched against the
branch's realised token. An unsubstituted literal `N` returns no match, so a model echoing the
template is not scored as rationalising.

**No LLM judge.** Using a second language model to adjudicate whether an explanation counts as
a rationalisation would reproduce, inside the instrument, the interpretive move the paper
criticises. Raw explanations ship verbatim for anyone who wants to score them differently.

## Analysis

Per-model primary; no pooling without homogeneity. Cluster bootstrap resamples **games**, since
probes within a game share a scenario and a state. Binomial verdicts use the **interval bound**,
not the point estimate, so an underpowered cell cannot pass on a lucky proportion, and a gate
with zero trials is reported UNRUN rather than passed — a missing row otherwise reads as a
test that succeeded.

The pre-registration names both an exact Clopper–Pearson interval and a cluster bootstrap over
games, and for the binomial gates the two disagree. Three readout paraphrases at two probe
points give six probes per game, and those six share a scenario and a state; Clopper–Pearson
treats them as six independent trials, so its interval is too narrow — anti-conservative in
exactly the direction that makes a gate easier to pass. **Both are reported.** The
Clopper–Pearson verdict stays primary because that is what was frozen, and a gate whose
clustered bound does not also clear the threshold is marked `DISAGREES` rather than quietly
resolved: choosing between them after seeing the data is the move the pre-registration exists
to prevent.

**State identity is checked against the records, not only claimed.** Every record carries a
digest of the state it was measured at, and the analysis refuses to run unless probes reported
as sharing a state carry one digest — and unless probes at different states carry different
ones, since a constant digest would pass the first check while measuring nothing.

Equivalence is a **one-sided upper bound** on a non-negative distance, against margins fixed
on substantive grounds before collection. It was written as a two-sided TOST, but total
variation and KL divergence are both non-negative, so the lower arm was vacuously true for
any data: the test was one-sided already, evaluated at the 2.5% tail and labelled as a 95%
TOST. That mislabelling was conservative rather than permissive — it could not manufacture a
false equivalence — but the instrument is now named for what it does.

Holm–Bonferroni is applied within each model's Tier-1 family, and the corrected decision is
reported beside the uncorrected interval.

Divergence is compared against `p_diverge` computed under **the sampler that actually produced
the draws** — computing it from the untruncated distribution overstated Qwen's C1 by 22×,
because once `p_max` exceeds `top_p` the nucleus admits one candidate (F9).
