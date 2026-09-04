# Experiment 1 — Tier-1 results

## gemma4_26b_moe

States probed: 320; branch-arm states: 240

| Test | Tier | n | proportion | 95% CP | 95% clustered | threshold | passed | Holm |
|---|---|---|---|---|---|---|---|---|
| G2_sensitivity | 1 | 240 | 1.0000 | [0.9847, 1.0000] | [1.0000, 1.0000] (40g, PASS) | min 0.9 | PASS | reject H0 |
| T5_false_recovery | 1 | 240 | 0.0458 | [0.0231, 0.0805] | [0.0083, 0.0917] (40g, PASS) | max 0.15 | PASS | reject H0 |
| T2_retrospective_follows_realised | 1 | 487 | 0.9877 | [0.9734, 0.9955] | [0.9760, 0.9978] (120g, PASS) | min 0.9 | PASS | reject H0 |
| T3_realised_choice_rationalisation | 1 | 487 | 1.0000 | [0.9925, 1.0000] | [1.0000, 1.0000] (120g, PASS) | min 0.9 | PASS | reject H0 |

Holm-Bonferroni is applied within this model's Tier-1 family; the
Clopper-Pearson column is the uncorrected 95% bound and is the
pre-registered verdict. The clustered column resamples **games**, since
six probes share a scenario and a state, so Clopper-Pearson treats
dependent trials as independent and is anti-conservative. A `DISAGREES`
marker means the gate passes only when that dependence is ignored.

Gates on continuous quantities (cluster bootstrap over games, not
an exact binomial: observations are nested inside games):

| Test | Tier | games | estimate | 95% CI | threshold | passed |
|---|---|---|---|---|---|---|
| G3_constraint_tracking | 1 | 40 | 0.3256 | [0.2185, 0.4373] | min 0.8 | FAIL |
| T4_reason_recovery_contrast | 1 | 5 | 1.0000 | [1.0000, 1.0000] | min 0.0 | PASS |

Candidate mass and entropy by condition (second outcome, never a filter):

| Condition | mean candidate mass | mean entropy (bits) |
|---|---|---|
| C0 early | 0.9998 | 2.0585 |
| C0 late | 0.9992 | 1.1583 |
| C1 early | 1.0000 | 0.0037 |
| C1 late | 0.9999 | 0.0275 |
| C2 early | 1.0000 | 0.0003 |
| C2 late | 1.0000 | 0.0022 |
| C4 early | 0.9998 | 2.2352 |
| C4 late | 0.9993 | 1.1238 |

Divergence from an identical state, **by condition** (pooling would
average together conditions designed to differ):

| Condition | states | observed | predicted (sampler) | predicted (raw) |
|---|---|---|---|---|
| C0 | 80 | 0.9250 | 0.9250 | 0.9752 |
| C1 | 80 | 0.0125 | 0.0125 | 0.0465 |
| C2 | 80 | 0.0000 | 0.0000 | 0.0266 |

Mean conditional probability by **index position** under C0. An index
is a pointer, so part of this is preference over positions rather
than over targets; the bare-value arm is the check on that.

| position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean p | 0.019 | 0.101 | 0.160 | 0.118 | 0.156 | 0.095 | 0.156 | 0.097 | 0.072 | 0.025 |

Edge (first and last) 0.022 against interior 0.120, a ratio of 0.18.

## qwen36_27b

States probed: 320; branch-arm states: 240

| Test | Tier | n | proportion | 95% CP | 95% clustered | threshold | passed | Holm |
|---|---|---|---|---|---|---|---|---|
| G2_sensitivity | 1 | 240 | 1.0000 | [0.9847, 1.0000] | [1.0000, 1.0000] (40g, PASS) | min 0.9 | PASS | reject H0 |
| T5_false_recovery | 1 | 240 | 0.4625 | [0.3981, 0.5278] | [0.4291, 0.5042] (40g, FAIL) | max 0.15 | FAIL | retain H0 |
| T2_retrospective_follows_realised | 1 | 343 | 0.9854 | [0.9663, 0.9953] | [0.9716, 0.9970] (120g, PASS) | min 0.9 | PASS | reject H0 |
| T3_realised_choice_rationalisation | 1 | 343 | 1.0000 | [0.9893, 1.0000] | [1.0000, 1.0000] (120g, PASS) | min 0.9 | PASS | reject H0 |

Holm-Bonferroni is applied within this model's Tier-1 family; the
Clopper-Pearson column is the uncorrected 95% bound and is the
pre-registered verdict. The clustered column resamples **games**, since
six probes share a scenario and a state, so Clopper-Pearson treats
dependent trials as independent and is anti-conservative. A `DISAGREES`
marker means the gate passes only when that dependence is ignored.

Gates on continuous quantities (cluster bootstrap over games, not
an exact binomial: observations are nested inside games):

| Test | Tier | games | estimate | 95% CI | threshold | passed |
|---|---|---|---|---|---|---|
| G3_constraint_tracking | 1 | 40 | 0.3495 | [0.2351, 0.4717] | min 0.8 | FAIL |
| T4_reason_recovery_contrast | 1 | 5 | 0.9900 | [0.9700, 1.0000] | min 0.0 | PASS |

Candidate mass and entropy by condition (second outcome, never a filter):

| Condition | mean candidate mass | mean entropy (bits) |
|---|---|---|
| C0 early | 0.9986 | 1.7150 |
| C0 late | 0.9993 | 1.0689 |
| C1 early | 0.9989 | 0.0153 |
| C1 late | 0.9998 | 0.0769 |
| C2 early | 0.9977 | 0.0119 |
| C2 late | 0.9995 | 0.1276 |
| C4 early | 0.9852 | 1.7882 |
| C4 late | 0.9949 | 1.2325 |

Divergence from an identical state, **by condition** (pooling would
average together conditions designed to differ):

| Condition | states | observed | predicted (sampler) | predicted (raw) |
|---|---|---|---|---|
| C0 | 80 | 0.7750 | 0.7749 | 0.9879 |
| C1 | 80 | 0.0250 | 0.0250 | 0.5509 |
| C2 | 80 | 0.0250 | 0.0250 | 0.5303 |

Mean conditional probability by **index position** under C0. An index
is a pointer, so part of this is preference over positions rather
than over targets; the bare-value arm is the check on that.

| position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean p | 0.066 | 0.087 | 0.088 | 0.347 | 0.113 | 0.078 | 0.055 | 0.066 | 0.072 | 0.028 |

Edge (first and last) 0.047 against interior 0.113, a ratio of 0.41.
