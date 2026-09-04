# Technical appendix — the inference harness

The harness is not shipped (see `README.md`). This describes it precisely enough to
reimplement, and records the facts a reader needs to judge the results. It mirrors the
paper's technical appendix.

## Environment

Apple M5 Max, 128 GB unified memory, macOS. `mlx==0.31.2`, `mlx-lm==0.31.3`,
`mlx-metal==0.31.2`, `transformers==5.5.0`, Python 3.12. Runtime dependency closure: 31
packages, no known vulnerabilities, gated on every build.

`transformers` is pinned to **5.5.0**, not the 5.4.0 running elsewhere on the collection machine:
5.4.0 is affected by CVE-2026-5241 / GHSA-fgcw-684q-jj6r (CVSS 9.6), where a LightGlue
config path lets `config.json` override `trust_remote_code=False`. We load neither LightGlue
nor remote code, so exposure was nil, but the fix is free. `trust_remote_code` is never
passed anywhere, and both checkpoints are pure safetensors — no pickle, no `.bin`, no `.py`,
nothing that executes on load.

`mlx-vlm` is deliberately **not** a dependency. It loads these checkpoints, but pulls
`fastapi`, `starlette`, `uvicorn`, `opencv-python`, `sounddevice`, `miniaudio`, `mlx-audio`,
`datasets` and `pandas` into the runtime closure of an experiment that serves no HTTP,
renders no images and plays no audio. Dropping it took the closure from 57 packages to 31.

## Models

| | Gemma 4 26B-A4B | Qwen 3.6 27B |
|---|---|---|
| Repository | `mlx-community/gemma-4-26B-A4B-it-qat-8bit` | `sprisa/Qwen3.6-27B-MLX-8bit-MTP` |
| Quantisation | 8-bit, quantisation-aware trained | 8-bit, post-training quantised |
| Layers / vocab | 30 / 262,144 | 64 / 248,044 |
| Cache | 25 `RotatingKVCache` (window 1024) + 5 `KVCache` | 48 `ArraysCache` (GatedDeltaNet) + 16 `KVCache` |
| Notes | `final_logit_softcapping = 30.0`; MoE, 128 experts, top-8 | MTP head stripped at load |

An asymmetry to state plainly: Gemma is QAT, Qwen is PTQ. There is no QAT Qwen 3.6. This
confounds family with quantisation method and forbids cross-family comparison of absolute
logit values. It does not threaten the primary claim, which is within-model.

## State, snapshot and branch injection

The apparatus is three primitives.

**Snapshot.** Per layer, capture `(class name, deep-copied state arrays, meta_state)`.
`mx.contiguous` is the load-bearing call: it produces a distinct array node that a later
in-place write cannot reach. Returning the array itself — or evaluating it and returning it
— hands back the live object.

This matters only for `RotatingKVCache`, and the distinction is subtle enough to have
produced a vacuous test suite. `KVCache.state` returns a *slice* `keys[..., :offset, :]`, so
a restored buffer has no slack and the next write reallocates; aliasing is invisible. Only
`RotatingKVCache` past rotation (`offset >= keys.shape[2]`) returns the **raw ring buffer**,
which `_update_in_place` writes into. A planted aliasing mutant survived an entire
model-driven suite because the fixture was a dense Llama with `KVCache`-only layers. The
regression tests now drive the cache classes directly with synthetic tensors.

**Restore** rebuilds through `_BaseCache.from_state`, deep-copying again on the way out so
branches are mutually independent. **Branch** is a context manager over a restored cache;
`append` is the only mutation path. Digests are BLAKE2b over layer order, class names,
meta-state and raw array bytes.

Two implementations exist and must agree bit-for-bit: in-memory copy, and a
`save_prompt_cache`/`load_prompt_cache` safetensors round-trip that cannot alias by
construction. The disk path is the ground truth.

## Ordering, and why sampling comes second

The full logit vector is recorded and digested **before** any RNG is initialised. Draws are
taken from the already-recorded distribution rather than by re-running the model — exact,
far cheaper, and it makes the ordering structural rather than remembered. Per-probe seeds
derive from the master seed via BLAKE2b, not Python's `hash`, which is randomised per
process and would make a recorded seed unreproducible.

Batch size is fixed at 1 throughout: batched forwards change matmul shapes and therefore
change floating-point results.

### Decoding, stage by stage

The paper's §2.2 design is T = 0 up to the reveal and T > 0 for the reveal, with §4.8
requiring full logits to be recorded before any RNG is initialised.

| Stage | Setting |
|---|---|
| Pre-reveal assistant turns | **Written by the harness from a fixed script; the model generates nothing.** Stronger than T = 0: greedy still makes the state depend on an argmax, whereas a harness-written transcript makes `S` identical by construction, verified by digest |
| Reveal | Model-card deployment sampler — Gemma `T=1.0, top_p=0.95, top_k=64`; Qwen non-thinking `T=0.7, top_p=0.80, top_k=20`; `min_p=0` on both |
| Retrospective and explanation probes | **Greedy.** Sampling them would confound the branch's realisation with a second sampling event; greedy makes each report a deterministic function of its branch, so T2 measures the branch alone |
| Repetition and presence penalties | **Disabled everywhere**, a declared deviation from the model cards. A repetition penalty is a logits processor that rewrites the distribution as a function of token history — the quantity under measurement. Target continuations are 1–3 tokens, so Gemma's repetition attractor is not a live risk |

**Sampling is over the candidate-restricted distribution.** For temperature this is exact:
the normaliser cancels, so `(exp(lᵢ)/Z)^(1/T)` renormalised equals `exp(lᵢ/T)/Σ_C exp(l_ⱼ/T)`
(verified to 1e-12). For top-p and top-k it is an **approximation**: deployment top-k selects
from a 262k-token vocabulary while ours is a no-op over ten candidates, and deployment top-p
cuts the full-vocabulary cumulative while ours cuts the candidate-conditional. Because
candidate mass is 0.9995–0.9999 the two agree to well under 0.1%, but it is
restrict-then-truncate rather than truncate-then-restrict and is recorded as such.

## Prompt construction

Transcripts are built at the **message** level and every extension asserts that the rendered
token sequence begins with the captured state's tokens. Chat templates do not guarantee
this: rendering with a generation prompt appends an assistant opener that a later user turn
replaces, so a state captured *with* it is not a prefix of any extension — and appending a
readout to it produces a doubled assistant turn. Raw token concatenation did exactly that,
and the model simply echoed; candidate mass rose from 0.0001 to 0.999 once fixed.

**Non-thinking** is asserted on the rendered string, not the kwarg, and the semantics are
the inverse of the obvious reading. Gemma with thinking *off* appends an empty, pre-closed
`<|channel>thought\n<channel|>` — the closed channel is the suppression; with thinking *on*
it injects `<|think|>` into a system turn. Qwen with thinking on ends at an unclosed
`<think>`. The rule covering both: no thinking trigger anywhere, and no reasoning channel
left open at the end.

The Qwen template injects `Current date: <today>` via `strftime_now`, which would change the
prompt — and therefore the state — between runs on different days. It is pinned through the
template's `date_string` override.

## Commissioning: faults found before the instrument worked

Ordinary instrument commissioning, recorded here because two are real upstream bugs others
will hit. None of them is a pre-registration deviation: no threshold, condition or analysis
rule changed, and no outcome informed any choice. Runs made before the instrument worked are
not results.

### 1. Mis-sanitised checkpoint weights (upstream)

`mlx_lm` 0.31.3's `models/qwen3_5.py::TextModel.sanitize` infers whether to apply the
HuggingFace→MLX RMSNorm convention shift (`w → w + 1`) from a proxy:

```python
should_shift_norm_weights = has_mtp_weights or has_unsanitized_conv1d
```

`sprisa/Qwen3.6-27B-MLX-8bit-MTP` retains its MTP weights, so the flag is set, but its norm
gains are already in MLX convention (measured mean ≈ 1.0). The shift doubles every RMSNorm
gain. The model loads cleanly, reports the correct architecture and cache composition,
passes every structural check — and emits fragments.

Corrected by deciding from the values rather than the proxy; the patch is a no-op for
checkpoints upstream already handles. Stage 0 now runs a coherence check — a factual question
that must be answered correctly. Structure is not function, and only generated text exposes
this class of fault.

That check is asked **through the chat template**, not as a raw completion. Both models are
instruction-tuned, and Gemma 4 has a documented weight-level repetition attractor that makes
it loop on bare completions (`" it is it is it is"`) while answering the same question
correctly in chat form. A completion-style check therefore failed a healthy model — a false
alarm that would teach a reader to ignore the gate it exists to arm.

### 2. Template-level thinking suppression is not model-level suppression

Qwen 3.6's template **omits** the think block when thinking is off; it does not close one.
The model, trained to open `<think>` regardless, does so with **p = 0.9988**, leaving
**0.0012** of probability mass on a bare answer. Every structural check passed in that state:
no open channel in the rendered prompt, correct tokenisation, 50/50 determinism, and perfect
recovery of the injected target *within* the candidate set. The readout was conditioning on a
0.1% event.

Gemma's template appends an empty, pre-closed block natively. Doing the same for Qwen — a
per-model `thinking_suppression_suffix` — restores candidate mass to **0.9996**. Stage 0 now
gates on `answers_with_a_candidate ≥ 0.5`.

This is a methodological point, not merely an implementation note: an experiment that
disables reasoning through the chat template and assumes it worked can be measuring a rare
conditional event with no indication that it is. `candidate_mass` is what reveals it, which
is why it is a reported outcome and not an exclusion filter.

### 3. Stale bytecode from the mutation harness

The mutation gate rewrites sources in place and restores them, but a `.pyc` compiled from the
*mutated* source can outlive the restore: these mutations preserve file size, and mtime
granularity is coarse enough that CPython may accept the stale bytecode. A subsequent run
crashed on a scenario its own tests were passing, because a mutated comparison was still live
in bytecode. `mutation_sanity.py` now purges `__pycache__` before and after every mutant.

A mutation harness that can leave poisoned bytecode behind is worse than none — the same
class of hazard as the mutmut misconfiguration that motivated choosing cosmic-ray.

### 4. Faults found by adversarial review of the finished code

Found by reading the code against its own claims rather than by a failing test. Listed
because each produced, or could have produced, an artifact that looked complete.

**C2 injected reasons that were false of their targets.** The reason was drawn uniformly
from four options regardless of which index had been injected, so roughly two thirds of C2
games asserted something like *"your secret choice is index 7. You chose it because it is
the first option in the list."* C2 exists to place a **genuine** reason in the state and ask
whether the readout recovers it; a reason that contradicts the target confounds
recoverability with willingness to repeat a falsehood, and this design cannot separate the
two. Reasons are now paired with the indices they hold of, and the pairing is asserted
against an independent restatement of each sentence rather than against itself. This
changed the collected data, so the Tier-1 records were recollected.

**Two runs could merge into one file.** `RecordWriter` opened for append, so re-running a
stage into a populated directory concatenated runs. The analysis rejects mixed pipeline
fingerprints — but two runs of the *same* source version carry the same fingerprint, so
they would have merged in silence and inflated every n. Now exclusive creation, failing at
write time where the operator can still choose a different directory.

**The fingerprint did not cover the prompts.** `FINGERPRINT_GLOBS` covered source and
configs but not the chat templates or the prompt bank, both of which are read at run time
and both of which change the rendered transcript. Editing a template would have produced
records claiming the fingerprint of the code that read it — a provenance claim that was
true about the wrong thing.

**Weight loading was resolved by sort order.** `snapshot_dir` returned the first snapshot
directory in sorted order, so with two revisions cached, which weights loaded depended on
how the hex digests happened to compare, and the manifest could name a revision the run did
not use. It now resolves through `refs/main` and refuses an ambiguous cache.

**A silent no-op in the upstream patch.** `apply_patches` returned `[]` when it could not
find its target. If upstream renames the heuristic the qwen3_5 patch keys on, the doubled
RMSNorm gains of fault 1 come back — and the model still emits fluent text, which is the
dangerous case. Load now raises for families that require a correction.

**Stage 0 could pass checks it never ran.** Two checks were emitted only when their config
key was present, and a missing row reads as a pass; two more were hardcoded `True`.
Softcapping is now recorded as an observation rather than scored as a passing check, and
the MTP assertion is executed here rather than reported as having been executed elsewhere.

**Analysis defects that changed reported numbers.** G3 used one `0.80` literal for two
unrelated quantities, inventing a two-level test the pre-registration never specified. T4
computed only C2's recovery rate while its own docstring described a contrast against C0.
Holm–Bonferroni was implemented and never called, so every gate was reported at nominal
95% while the pre-registration claims family-wise correction. All three are corrected, and
the Tier-1 numbers in `results/` are the corrected ones.

## Numerical reproducibility: what is exact and what is not

Two different claims are often run together, and only one of them is exact.

**Branch against branch is bit-identical.** Branches restored from one snapshot and given
the same tokens produce the same bits. This is the Tier-1 claim — state identity — and it
holds at the strongest available standard, asserted by test rather than by tolerance.

**Branch against a single uncached forward pass is not.** Writing that test as an exact
equality was the first thing tried, and it fails. A single pass over *n* tokens runs one
matmul of shape `(1, n, d)`; the branch arm runs the prefill and the appended turn as two,
and floating-point reduction is not associative, so a different tiling accumulates in a
different order. Splitting the prefill at a third point gives a third answer.

This is the same phenomenon as the batch-size pin in §4.4, along the sequence axis instead
of the batch axis. It is a property of the hardware, not a defect in the snapshot.

Measured on the fixture model: raw logits differ by up to 0.34 in bfloat16, but the induced
candidate distribution moves by a total variation of **0.0079**, and the candidate argmax
does not move. The pre-registered T9 equivalence margin is 0.10, so arithmetic noise sits
more than an order of magnitude below the band the Tier-2 tests judge real effects against.
The test asserts a bound at half that margin, which is a real constraint rather than a
formality.

The practical consequence is a caveat rather than a correction: a recorded logit is exact
*for a given prefill chunking*, and the chunking is fixed by the pipeline. Anyone
recomputing these logits by feeding the full transcript in one pass should expect agreement
to about three decimal places in probability, not to the bit.

## Determinism

§4.8 requires identical raw logits after identical state restoration. Most of the pipeline
is exact by construction — safetensors loading is byte-exact, Q8 affine dequantisation is a
deterministic function of exact stored values, and cache round-trips are lossless. The one
open question was GPU floating-point reduction order.

**Measured: 50/50 identical full-logit digests for both models**, at batch size 1 in the
windowed regime. Rung 1 of the pre-registered ladder.

Separately: cache reuse is *not* numerically identical to a full recompute of the same
tokens — these are legitimately different computations, and the gap is quantified above
rather than asserted away. Snapshot-and-branch agrees with plain cache reuse exactly, which
is the property the experiment needs.

## The bare-value arm

Stage 3 answers the limitation the pre-registration discloses in advance: an index is a
pointer, so a readout over indices may measure pointer preference rather than target content.

Options are rendered as fixed-width two-digit values with **no index labels**, and the
readout asks for the number. Scoring uses a prefix trie over all 100 values via the chain
rule — `score(c) = Σ_t log P(c_t | H, R, c_<t)` — which costs 11 forward passes per probe
instead of 100 and is exactly equivalent. Fixed width means no length normalisation is
needed. Stage 0 verifies that every digit is a single token for each model, and the stage
refuses to run otherwise: a tokeniser that merged digit pairs would put the chain rule on the
wrong boundaries and every candidate score would be wrong while still looking like a
distribution.

Records carry the **whole** 100-value space plus `option_values`, the ten actually shown.
Keeping only the ten would make `1 − candidate_mass` ambiguous between two different facts —
the model preferring a number it was never offered, and the model not answering with a number
at all. Both are recoverable as shipped.

The transcript is otherwise identical to the index arm and is asserted by test to differ in
exactly one message. C1's injected target names the *value* rather than the index, since with
no labels in the transcript an index would refer to nothing the model can see.

## Quality controls

Two independent stacks — harness and analysis — with separate virtualenvs, lockfiles,
Makefiles, cosmic-ray sessions and mutation lists, and no cross-imports beyond the record
schema. Each runs ruff, `ruff format --check`, `mypy --strict`, pytest with property-based
tests, cosmic-ray, and a fast hand-written mutation gate in which a surviving mutant is
treated as a vacuous test — 24 hand-written mutants across the two suites, all killed, each
one a specific way of being wrong that a passing test suite had previously tolerated. A
dependency gate fails the build on any CVE, on forbidden runtime categories, or on closure
growth past a declared budget; it runs against **both** packages, since the analysis package
is the one a third party installs. A containment linter rejects any import or path escaping
the project. Every gate runs in CI on every push, not only by hand.
