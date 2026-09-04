# Experiment 1 — Tier-2 (mechanism) and Tier-3 (Luo replication)

**These do not bear on Tier 1.** Tier 1 rests on state identity; a failure here is a
finding about the readout distribution, not about the causal demonstration.

Regimes are reported separately. Equivalence is a **one-sided upper bound** on a
non-negative distance, not a symmetric interval — see `stats.equivalence_upper_bound`.

**T10's KL magnitude is not interpretable; its verdict is.** The value is dominated
by `m · log2(m / floor)`, where `m` is the readout mass falling outside the
constraint-consistent set and `floor` is the probability assigned to an excluded
candidate. At the measured m ≈ 0.67, a floor of 1e-3 gives 6.3 bits and 1e-9 gives
19.8 — the number describes the floor. The verdict is robust for any floor small
enough to mean "excluded", and `T10_tv` reports the same comparison in total
variation, which has no floor to choose and is bounded in [0, 1].

## gemma4_26b_moe

| Test | Tier | n games | dropped | estimate | 95% upper bound | margin | within |
|---|---|---|---|---|---|---|---|
| T9_commitment_framing_adds_nothing[D] | 2 | 40 | 0 | 0.2524 | [0.2238, 0.2823] | 0.1 | NO |
| T10_prior_times_constraints_vs_C6[D] | 2 | 40 | 0 | 14.0214 | [13.1049, 14.9283] | 0.15 | NO |
| T10_tv_prior_times_constraints_vs_C6[D] | 2 | 40 | 0 | 0.7842 | [0.7362, 0.8312] | 0.1 | NO |
| T9_commitment_framing_adds_nothing[U] | 2 | 10 | 0 | 0.2295 | [0.1920, 0.2688] | 0.1 | NO |
| T10_prior_times_constraints_vs_C6[U] | 2 | 10 | 0 | 5.0339 | [3.6969, 6.3834] | 0.15 | NO |
| T10_tv_prior_times_constraints_vs_C6[U] | 2 | 10 | 0 | 0.4853 | [0.4166, 0.5543] | 0.1 | NO |

**Tier 3 — Luo override framing, per condition and per probe.** TV between the SUDO-override readout and the neutral readout at the *same condition and state*. Pooling conditions here produced a retracted finding. `R0` is their Number Guessing clause (Listing 1), which is the task replicated here; `R0S` is the stronger Entity Guessing clause (Listing 3) run on the same scenario, so the pair isolates instruction strength from override framing. They are never pooled.

| Condition / override probe | n games | mean TV | 95% upper bound |
|---|---|---|---|
| C0/R0 | 40 | 0.3511 | [0.3114, 0.3917] |
| C0/R0S | 40 | 0.3867 | [0.3353, 0.4389] |
| C1/R0 | 40 | 0.0029 | [0.0001, 0.0083] |
| C1/R0S | 40 | 0.0029 | [0.0001, 0.0083] |
| C2/R0 | 40 | 0.0001 | [0.0000, 0.0003] |
| C2/R0S | 40 | 0.0002 | [0.0001, 0.0003] |
| C4/R0 | 40 | 0.8724 | [0.8314, 0.9074] |
| C4/R0S | 40 | 0.7983 | [0.7475, 0.8468] |

**Tier 2 — elicitation robustness.** Paraphrase agreement is mean pairwise
`1 - TV` across the neutral paraphrases at one state; the override probe is
excluded, since it carries a system clause the others do not and pooling it
would report a framing effect as paraphrase noise. Turn drift is TV between the
early and late readouts at the same state and paraphrase — it *should* move,
since the constraints entering the context are new information.

Agreement is reported against its chance baseline: a concentrated readout
produces high agreement with no stability whatsoever, so the number to read is
the gap between paraphrases and what two draws from a *single* paraphrase
would already show (Lanham et al. 2023, App. B).

| | estimate | 95% upper bound |
|---|---|---|
| paraphrase agreement, mean 1 - TV (C0) | 0.8770 | [0.8665, 0.8869] |
| — as draw agreement, observed | 0.4270 | [0.3985, 0.4554] |
| — chance baseline (two draws, one paraphrase) | 0.4401 | [0.4122, 0.4684] |
| turn drift, early → late (C0) | 0.7829 | [0.7224, 0.8387] |

**Tier 3 — what Luo et al.'s top-20 truncation contributes.** Their pipeline
keeps the top 20 vocabulary logits and assigns -9999 to the rest, so a candidate
that drops out of the window does not become unlikely, it becomes impossible —
and a KL against a zero is unbounded. The same early→late KL is computed both
ways on the same states. `sudo_override` is their own probe, which is the row
that bears on their reported numbers; `neutral` is ours, reported beside it.

| probe | states | a candidate truncated | KL literally infinite | mean KL, full support | mean KL, truncated |
|---|---|---|---|---|---|
| R0 | 40 | 0 | 0 | 3.5114 bits | 3.5114 bits |
| R0S | 40 | 2 | 0 | 3.8560 bits | 3.8560 bits |
| neutral | 120 | 1 | 0 | 4.3742 bits | 4.3742 bits |

The means exclude the infinite cases, which are counted instead: a mean containing an infinity is infinite, and the count says more.

## qwen36_27b

| Test | Tier | n games | dropped | estimate | 95% upper bound | margin | within |
|---|---|---|---|---|---|---|---|
| T9_commitment_framing_adds_nothing[D] | 2 | 40 | 0 | 0.2777 | [0.2586, 0.2973] | 0.1 | NO |
| T10_prior_times_constraints_vs_C6[D] | 2 | 40 | 0 | 14.0434 | [12.8835, 15.1529] | 0.15 | NO |
| T10_tv_prior_times_constraints_vs_C6[D] | 2 | 40 | 0 | 0.7744 | [0.7141, 0.8320] | 0.1 | NO |
| T9_commitment_framing_adds_nothing[U] | 2 | 10 | 0 | 0.2641 | [0.2461, 0.2838] | 0.1 | NO |
| T10_prior_times_constraints_vs_C6[U] | 2 | 10 | 0 | 6.7893 | [5.7277, 7.8172] | 0.15 | NO |
| T10_tv_prior_times_constraints_vs_C6[U] | 2 | 10 | 0 | 0.5539 | [0.4755, 0.6305] | 0.1 | NO |

**Tier 3 — Luo override framing, per condition and per probe.** TV between the SUDO-override readout and the neutral readout at the *same condition and state*. Pooling conditions here produced a retracted finding. `R0` is their Number Guessing clause (Listing 1), which is the task replicated here; `R0S` is the stronger Entity Guessing clause (Listing 3) run on the same scenario, so the pair isolates instruction strength from override framing. They are never pooled.

| Condition / override probe | n games | mean TV | 95% upper bound |
|---|---|---|---|
| C0/R0 | 40 | 0.2402 | [0.2124, 0.2698] |
| C0/R0S | 40 | 0.1681 | [0.1431, 0.1948] |
| C1/R0 | 40 | 0.0071 | [0.0035, 0.0117] |
| C1/R0S | 40 | 0.0072 | [0.0036, 0.0118] |
| C2/R0 | 40 | 0.0095 | [0.0056, 0.0139] |
| C2/R0S | 40 | 0.0095 | [0.0057, 0.0140] |
| C4/R0 | 40 | 0.6530 | [0.6207, 0.6788] |
| C4/R0S | 40 | 0.6530 | [0.6203, 0.6793] |

**Tier 2 — elicitation robustness.** Paraphrase agreement is mean pairwise
`1 - TV` across the neutral paraphrases at one state; the override probe is
excluded, since it carries a system clause the others do not and pooling it
would report a framing effect as paraphrase noise. Turn drift is TV between the
early and late readouts at the same state and paraphrase — it *should* move,
since the constraints entering the context are new information.

Agreement is reported against its chance baseline: a concentrated readout
produces high agreement with no stability whatsoever, so the number to read is
the gap between paraphrases and what two draws from a *single* paraphrase
would already show (Lanham et al. 2023, App. B).

| | estimate | 95% upper bound |
|---|---|---|
| paraphrase agreement, mean 1 - TV (C0) | 0.8928 | [0.8783, 0.9067] |
| — as draw agreement, observed | 0.4862 | [0.4473, 0.5275] |
| — chance baseline (two draws, one paraphrase) | 0.4984 | [0.4612, 0.5375] |
| turn drift, early → late (C0) | 0.8137 | [0.7487, 0.8722] |

**Tier 3 — what Luo et al.'s top-20 truncation contributes.** Their pipeline
keeps the top 20 vocabulary logits and assigns -9999 to the rest, so a candidate
that drops out of the window does not become unlikely, it becomes impossible —
and a KL against a zero is unbounded. The same early→late KL is computed both
ways on the same states. `sudo_override` is their own probe, which is the row
that bears on their reported numbers; `neutral` is ours, reported beside it.

| probe | states | a candidate truncated | KL literally infinite | mean KL, full support | mean KL, truncated |
|---|---|---|---|---|---|
| R0 | 40 | 0 | 0 | 4.5725 bits | 4.5725 bits |
| R0S | 40 | 0 | 0 | 5.6008 bits | 5.6008 bits |
| neutral | 120 | 0 | 0 | 5.2553 bits | 5.2553 bits |

The means exclude the infinite cases, which are counted instead: a mean containing an infinity is infinite, and the count says more.
