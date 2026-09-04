# Deceptive mechanism — replication package

Data, prompts, pre-registrations and analysis code for [*From Deceptive Outputs to Deceptive
Mechanisms: A Causal Framework for Language-Model Deception
Research*](https://arxiv.org/abs/2609.04166) (arXiv:2609.04166).

The paper argues that behaviour which looks deceptive does not license claims about deceptive
mechanisms, and that evidence at one causal level does not establish the next. Five experiments
test that on two open-weight model families. This repository is the evidence behind them.

**Version 1.0.0** · built 2026-09-03 · source commit `52fb835` · 31,168 records.
Cite the paper ([arXiv:2609.04166](https://arxiv.org/abs/2609.04166)), not this repository, for the results themselves.

**Please read [`DISCLAIMER.md`](DISCLAIMER.md) first.** Every organisation, person, email address
and ticker in the scenarios is fictional and refers to no real party.

## Where to start

| you want | read |
|---|---|
| what was found, per experiment | `replication_package/experiment*/results/FINDINGS.md` |
| what was promised before collection | `replication_package/experiment*/PREREGISTRATION*.md` |
| the exact prompts the models saw | `replication_package/PROMPTS.md` |
| where every file is and what regenerates each number | `replication_package/REPLICATION_GUIDE.md` |
| the numbers that must not be quoted, and why | the "Numbers that must not be quoted" section of each `FINDINGS.md` |

Each `FINDINGS.md` opens with a headline, states what the result does and does not establish, and
lists figures that must not be quoted without their restriction. Those lists are not decoration:
they record where an earlier draft of the paper overstated something, and what the correct
statement is.

## What is not redistributed

Three classes of file are described in this package but deliberately not shipped, to keep the
download small. No reported number depends on any of them.

| not shipped | what it was | where it is described |
|---|---|---|
| `*_INVALID_*.jsonl` | runs made before the instrument worked | `experiment1/DATASHEET.md`, `APPENDIX_TECHNICAL.md` |
| `*_SUPERSEDED_pre_review.jsonl` | runs of a working instrument that review later corrected | `experiment1/DATASHEET.md` |
| `*.run1_failed.*` | a failed Experiment 5 collection, kept in the authors' archive | `experiment5/results/FINDINGS.md` |
| `experiment1/BACKGROUND.md` | pre-experiment reading notes: the paper's own argument, and an annotated bibliography summarised largely at second hand | the paper's related-work section covers the same ground, from checked sources |

Several documents here say these runs "are retained for inspection". That is true of the
authors' complete archive, which these documents also describe; it is not true of this public
package. The faults that produced each class are written up in full, which is the part a reader
needs in order to judge them. The collection harness is likewise not shipped, for the separate
reason given at the end of `replication_package/FILE_GUIDE.md`.

## The data

Records are one JSON object per line, gzipped. Decompress before analysing:

```
gunzip -k replication_package/experiment*/data/*.jsonl.gz
gunzip -k replication_package/experiment1/data/records/*.jsonl.gz
```

Every record follows `replication_package/experiment1/schemas/probe_record.v1.json`, the one
contract shared between the collection harness and the analysis. Each data directory also carries
a manifest naming the model revisions, package versions and pipeline fingerprint of the run that
produced it.

**Superseded and failed runs are not shipped here.** Two collections were discarded during the
programme: an Experiment 5 run that failed its manipulation checks, and Experiment 1 records
collected before a probe-wording correction. What they were, why they were discarded and what
changed as a result are recorded in the findings and pre-registrations, which is the part a reader
needs. The record files themselves are large, and no result reported in the paper was computed from them.

## Running the analysis

```
cd replication_package/experiment1/analysis
uv sync
uv run pytest                      # the invariants the analysis must satisfy
```

`replication_package/REPLICATION_GUIDE.md` names the function that regenerates each headline
number. Analysis code is here; the collection harness is not, because it is bound to one machine
and one accelerator stack, and the records plus manifests are what reproduction needs.

## What is not claimed

Results are statements about the immediate conditional policy under this inference protocol,
measured from logits without decoding, on two named models, never pooled across them. They are not
claims about those models under arbitrary inference budgets, and not claims about language models
in general.

## Citation

Cite the paper. This repository is its evidence, not a separate result.

> Shkolnikov, Y. P. (2026). *From Deceptive Outputs to Deceptive Mechanisms: A Causal Framework
> for Language-Model Deception Research*. arXiv:2609.04166 [cs.AI].
> <https://doi.org/10.48550/arXiv.2609.04166>

```bibtex
@misc{shkolnikov_deceptive_2026,
  title         = {From Deceptive Outputs to Deceptive Mechanisms: {A} Causal Framework for
                   Language-Model Deception Research},
  author        = {Shkolnikov, Yakov Pyotr},
  year          = {2026},
  eprint        = {2609.04166},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  doi           = {10.48550/arXiv.2609.04166},
  url           = {https://arxiv.org/abs/2609.04166}
}
```

## Licence

MIT, see [`LICENSE`](LICENSE). The scenarios reconstruct a published environment; attribution and
the limits of that reuse are in `replication_package/experiment1/prompts/LICENSING.md`.
