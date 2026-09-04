# Known instrument defects

A pre-release audit of the collection harness and the analysis package. Everything below was
verified against the shipped records, not inferred from the code alone. Each entry states its
exposure and whether it moves a number reported in the paper.

Several entries name modules of the collection harness — `scenarios/commitment.py`,
`pipeline/stage09_provenance.py`, `tests/unit/test_sampler.py`. **The harness is deliberately not
shipped**; see the note at the end of `FILE_GUIDE.md` for why. The records, manifests and analysis
code that *are* shipped are enough to re-derive every figure quoted below, and every one of them
was re-derived that way for this audit.

Two entries move a reported number. Both are in Experiment 4, both are also written up in
`experiment4/results/FINDINGS.md`, and one of them has a known, conservative direction. The
rest are metadata and documentation defects that no reported statistic depends on.

## 1. The commitment detector matched inside longer words — MOVES A NUMBER

`scenarios/commitment.py` matched a bare `yes`/`no` without a trailing word boundary, so `no`
matched inside `not`, `nothing`, `know` and `unknown`. A sentence saying "I must answer as if
I did not know" was read as committing to an answer.

**Exposure.** The cut is taken at a sentence boundary, so nothing was ever cut mid-word: the
effect is a cut taken *too early*, before a sentence that had committed to nothing. Re-running
the corrected rule over all 864 collected trajectories moves the cut on 22 of them — 8 Gemma,
14 Qwen — and every one was cut short. That is 22 of the 824 truncated records, 2.7 %.

**Direction is known and favours the null being rejected less easily.** Retaining less of a
trajectory removes more leakage, and the truncated regime already yields the lowest contrast of
the four. Correcting the cuts lengthens the prefixes and moves the truncated estimates *up*,
towards the untruncated ones and further from the ±0.05 equivalence margin. The reported
figures — about 36 points (Gemma) and 29 (Qwen) — are therefore conservative for the
"not derived" conclusion, not favourable to it. The paper's description of the operation
("cutting each trajectory before its first answer-committing sentence") remains literally true,
since cutting early is still cutting before that sentence.

**The independent detector shared the defect.** `deceit_analysis.judging` carried the same
pattern, so the cross-stack audit of answer leakage was not independent *on this point*. Both
are fixed, with a test. Recomputed leakage: 373/432 = 86.3 % (Gemma), 378/432 = 87.5 % (Qwen),
against 87.0 % and 87.7 % as published. The paper's "about 87 per cent" stands.

## 2. Stage 9 applied temperature before truncation — MOVES A NUMBER

`stage09._sampler` divided the logits by the temperature and *then* applied top-k / top-p /
min-p, so top-p measured its mass on an already-sharpened distribution and kept a smaller
nucleus than the model card specifies. mlx_lm, the stack these weights are served by, truncates
the raw logprobs and tempers last inside `categorical_sampling`; so does this project's own
`stage01.sample_realisations`. The two harness samplers disagreed with each other and stage 9
was the one that was wrong.

This is the same fault `tests/unit/test_sampler.py` already records in its docstring against
`sample_realisations`, where it once made a top-p 0.80 prediction overshoot twenty-fold. It was
fixed there and missed here.

**Exposure is one model and one arm.** At `temperature = 1.0` the two orders are the same
function, so **Gemma is unaffected in full**. Qwen runs at 0.7 with `top_p = 0.80`: its 432
reasoning trajectories were drawn from a sharper distribution than declared. The direct-readout
condition samples nothing — every `sampler_role` there is `none` — so the **headline provenance
contrasts, +48 points (Gemma) and +24 (Qwen), do not depend on this at all**.

**It is not a differential between the arms.** All three provenance conditions drew trajectories
through the same sampler, so the defect shifts the distribution the contrast is measured over,
not the contrast between conditions. The size of any resulting shift is unmeasured and needs a
re-run with the models. Unlike defect 1, its direction is not signable from the records, so it
is an open limitation rather than a conservative one.

Fixed, with three tests pinning the order; one fails against the old code.

## 3. Experiment 4 trajectories are not reproducible from the shipped code

Two independent reasons, so this is stated separately from defect 2.

- The Qwen trajectories were collected under the pre-fix sampler order.
- `sampler_seed` on the Experiment 4 reasoning records holds the **trajectory index** — 0, 1 or
  2, on 864 records, and `None` on the remaining 432 — not the RNG seed that drew the
  trajectory. All four `sampler_*` parameter fields are `None` on every Experiment 4 record,
  including the reasoning ones.

The trajectory text itself *is* shipped, inside each record's `explanations` field, so every
downstream result remains checkable and every claim in this file was re-derived from it. What
cannot be done is redrawing the same trajectories from the same seeds.

## 4. Ten of fifteen manifests record a dirty working tree

`git_commit` ends in `-dirty` in these manifests, so the code state at collection is not pinned
to a clean commit:

`experiment1/data/manifests/stage00_env_gate.json`, `experiment1/.../stage04_turn_resolved.json`,
`experiment3/data/manifests/stage06_rotated_gate.json`, `experiment3/data/stage07_utility.json`,
`experiment3/data/stage11_utility_rerun.json`, `experiment4/data/stage09_provenance.json`,
`experiment4/data/stage10_rerendered.json`, `experiment4/data/stage10_truncated.json`,
`experiment5/data/stage08_recipient.json`, and the failed Experiment 5 run's manifest, which is
not redistributed in the public package.

The remaining five are clean. This does not affect any computed value — every reported number is
recomputable from the shipped records — but it weakens provenance for anyone reconstructing the
collection environment.

## 5. C5 is probed twice at identical state

C5 supplies nothing beyond the marginal prior and has no acknowledgement turn and no question
tail, so nothing distinguishes its early probe from its late one. Every C5 instance probed at
both points has a byte-identical `logit_digest`: 100 of 100 checked. The 1600 C5 rows therefore
carry 800 distinct states.

This is a consequence of the design rather than a coding error, but it matters wherever early
and late C5 rows are pooled, because the effective sample size is half the row count. It is the
reason C6 exists: C6 was added as a structure-matched prior precisely because C5 is a two-message
prompt by construction. **No reported statistic pools C5 across probe points**, and the paper
attaches no number to C5 — Appendix B describes what it supplies and nothing more.

Separately, and not about C5: T10 aggregates over both probe points. The prior it uses is C6,
not C5, and `_index` keys records by (game, probe point, readout), so early and late are matched
pairwise rather than pooled into one distribution — but the reported figure averages the two.
Recomputed from the shipped records, in regime D:

| | Gemma | Qwen |
|---|---|---|
| T10 TV, as reported (both probe points) | 0.784 | 0.774 |
| early only | 0.894 | 0.898 |
| late only | 0.674 | 0.651 |

The reported value sits between the two, and late-only is the more conservative reading. Every
one of these is far outside the 0.10 margin, so the equivalence verdict is unchanged under any
of the three. T10 is not quoted in the paper.

## 6. `p_diverge` on the record is the raw-conditional quantity

The record field is computed from the raw conditional distribution rather than from the
distribution the sampler actually induces. This is already handled and already documented: the
analysis computes both, keeping the record's value as `*_predicted_raw` and deriving the
sampler-induced value separately in `tier1._sampler_p_diverge`, and `metrics.py` states the
distinction in its docstring. The field name remains misleading on its own.

## 7. Experiment 4 leaves the windowed regime for two Gemma trajectories

Not a defect; a scope note, because the caveat is currently documented only against
Experiment 3.

Experiments 1 and 2 held every prompt below Gemma's 1024-token sliding window
(`max_prompt_tokens = 900`), so `RotatingKVCache` never rotated and "exact state" was
unambiguous. That is constraint C-1, and it is why the determinism result is reported as
50/50 identical digests *in the windowed regime*. Experiment 4 uses
`trading_max_prompt_tokens = 4000` and appends up to 768 generated tokens, so C-1 does not
extend to it.

Measured from the shipped trajectories, re-tokenised with the model's own tokenizer:

| Gemma, Experiment 4 | |
|---|---|
| reasoning trajectories | 432 |
| longest snapshot state | 295 tokens |
| median peak context (state + trajectory) | 528 tokens |
| peak contexts at or above the 1024 window | 1 (at 1032) |
| trajectories that hit the 768-token cap | 2, matching the manifest |

Every snapshot is taken at most 303 tokens deep, far below the window, so no snapshot was
ever captured from a rotated buffer and hazard H-1 had no opportunity to fire. The single
crossing happens during generation on a branch, eight tokens past the window, in the model's
own native sliding-window attention.

**The regime it enters is validated.** `stage06_rotated_gate` exercises exactly this on the
real Gemma at 1500 and 3000 prompt tokens, asserts that rotation actually occurred (25 layers
past rotation) before measuring anything, and reports 50 restorations yielding a single
distinct logit digest with the snapshot unperturbed. Experiment 4's worst case sits well
inside that envelope. Qwen never rotates at all: its cache is `ArraysCache`, and the gate
records `applicable: false` rather than claiming a pass.

## 8. Items with no exposure in this collection

Verified as real but unreachable by any shipped result: re-rendering a trajectory through the
Qwen chat template can silently delete it; `score_sequences` compares forward passes of
different lengths; `generate`'s stop set is the turn terminator rather than the model's full
eos set. Each is a latent hazard for future collections rather than a defect in these results.

`reasoning_tokens_generated` is a whitespace word count, not a token count — 90 309 against a
true 123 547 for Gemma. No reported number uses it.
