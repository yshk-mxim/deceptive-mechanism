# Prompt provenance and licensing

Every prompt file in this directory, where it came from, and what may be done with it.

## `readout.toml`

| Section | Origin | Licence |
|---|---|---|
| `readout.R1`–`R8` | **Original to this work.** Neutral paraphrases written for Experiment 1 | MIT, with the package |
| `explanation.X1`–`X3` | **Original to this work** | MIT, with the package |
| `readout.R0` | **Derived from Luo et al. 2026**, arXiv:2603.25187, §3.2 and **Listing 1** | See below |
| `readout.R0S` | **Derived from Luo et al. 2026**, §3.2 and **Listing 3** | See below |

### R0 and R0S — the SUDO-override probes

`R0` reproduces the retrospective probe (their §3.2) and the system-prompt override clause
from **Listing 1, the Number Guessing Proposer prompt**. Number guessing is the task this
experiment replicates, so Listing 1 is the correct source.

`R0S` carries the clause from **Listing 3, the Entity Guessing Proposer prompt**, which is
materially stronger — *"CRITICAL RULE … IGNORE ALL OTHER INSTRUCTIONS"* against Listing 1's
*"temporarily ignore all other instructions for this single response"*. It is run on the
number-guessing scenario, so it is **not** a replication of their entity task; it isolates
whether the *strength* of the override instruction, rather than the fact of an override
framing, is what moves the readout. The two are never pooled.

An earlier version of this package used Listing 3's clause as `R0`, which measured a stronger
instrument than the one being replicated. The correction is recorded in
`results/FINDINGS.md` and the source of each clause is asserted by test.

Both are included because Tier 3 measures **their instrument**, and paraphrasing it would
defeat the purpose: the question is whether that specific framing changes the readout, which
cannot be asked about a reworded version.

**Reconstruction note.** Listing 1 as printed says *"When you see this exact phrase"* without
printing the phrase in the same block. The probe text is taken from their §3.2, which gives it
verbatim, and the SUDO USER is introduced using Listing 1's own closing sentence, which refers
to *"the SUDO USER as required"*. That join is ours, and it is flagged rather than presented as
quotation.

Their paper releases no code or data — the NeurIPS checklist states the authors "will
open-source the data and code when the paper is accepted" — but Listings 1–5 print the
prompts in full, so the paradigm is reconstructable from the published text. The excerpt here
is short, attributed, and used for direct scientific comparison.

Anyone redistributing this file should keep the attribution in `readout.toml` intact.

## Prompt-hygiene criterion

Every entry carries a `hygiene` field recording the check applied, after Cooney et al. 2026
(App. B.1): *"light prefills such as 'The answer is' may well be argued to not modify a model
belief, but specific prefills that contain part of the answer may instead modify model
beliefs."*

The criterion, fixed before collection: **an injected suffix may constrain the answer's
*form* but must be uninformative about its *content*.** So "Answer with the index only" is
admissible; "answer with an index between 0 and 4" is not. Candidate enumeration appears only
inside the ordering sub-study, where the enumeration *is* the manipulation and is analysed as
such.

`R0` is marked `not_neutral_by_construction` — it is the instrument under test, not a neutral
probe, and is never pooled with the neutral paraphrases.

## Scenario prompts

The guessing-game scenarios in `configs/experiment1.toml` and
`harness/src/deceit_harness/scenarios/` are original. They follow Luo et al.'s **candidate
scheme** — ten values drawn from 0–99, presented as single-token indices 0–9 — for
comparability, but the cover stories, question generation and conditions are ours.

## Not reproduced here

Material from Scheurer et al., Lanham et al., Mahon and Davidson is **cited, never copied**.

**The Scheurer canary, corrected 2026-09-02.** This section previously said their canary strings
"must be reproduced verbatim" once Experiment 3 derived from their scenario, and a related note in
`trading_task.py` said the canary was not in the paper and had to be obtained separately. Both
were wrong on the facts. Their Appendix A.1 prints two GUIDs in the PDF itself, and their request
is that the canary travel with **their data**. Experiment 3's scenario is a structural
reconstruction written from the published description, not a copy of their files, so stamping
their GUID on it would assert their provenance over text they did not write. What remains open is
an editorial decision rather than a missing dependency: carry their canary on anything that
reproduces their text, and mint a separate one for this package's own scenarios. Recorded as an
open decision in the authors' tracker. Probe `P1` is the one piece of their text used here, and it is excerpted with
attribution rather than reproduced in full.

## Chat templates

`harness/data/chat_templates/` holds copies of Google's current Gemma 4 template and a Qwen
3.6 template, with their sha256 digests recorded in the harness's own template directory. They are **copied rather than referenced** so that an edit elsewhere on
the machine cannot change our rendered prompts mid-study. They carry their upstream licences;
neither is original to this work.

## Entity names and email domains in the trading scenario (verified 2026-09-02)

**Instance 0 is theirs, not ours.** Scheurer, Balesni & Hobbhahn 2023 (arXiv:2311.07590) print the
scenario entities and addresses in their own paper. Counted in their PDF: `WhiteStone` 9 times,
`Alpha` 24, `Amy` 11, `Sally` 10, `LING` 23, and the addresses `sally@whitestone.com` (8
occurrences), `amy@whitestone.com` (6) and `william@whitestone.com` (1). Their other scenarios use
`gray.com`, `gladwell.com` and `bluedovecorp.com`. Our instance 0 reconstructs theirs, so it
introduces no exposure their publication did not already create.

**Instances 1-23 are ours, and this is the part to look at.** `Surface` carries a firm name and the
harness derives the address mechanically as `{name}@{first word of firm}.com`
(`trading_task.py`). That convention invents 23 further domains, and a DNS check on 2026-09-02
found **22 of 23 live with MX records** — only `thornbury.com` does not resolve. So the package
publishes fictional insider-trading transcripts naming addresses at real, mail-accepting domains
that have nothing to do with this work.

**Not changed here, deliberately.** The collected records embed these strings, and the shipped
prompts must regenerate byte-identically from the scenario code; editing the wording now would
break the correspondence between prompts and data that the package exists to provide. The options
are an author decision, still open: disclose and leave the instrument alone, or
move future collections to a reserved domain (RFC 2606 `example.com`, or RFC 6761 `.example`,
which can never resolve) and record it as a deviation.
