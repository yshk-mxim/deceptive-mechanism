# Experiment 1 — bare-value robustness arm (Tier 2)

Options shown as fixed-width two-digit values with **no index labels**; the readout
is scored over all 100 values by a prefix trie. `option mass` is the probability the
model puts on answering with one of the ten values it was actually shown — the
question the index arm cannot pose, since there every candidate is an option.

**Tier 2. This cannot disturb Tier 1**, which rests on state identity and holds in
either answer space.

## gemma4_26b_moe

States: 240

**Sensitivity (C1 recovery over values): 160/160 — PASS.** Without this, nothing else on this page is interpretable.

| Condition | answers with a number | of that, an offered value | mass on the consistent value | entropy (bits) |
|---|---|---|---|---|
| C0 early | 0.9998 [0.9998, 0.9998] | 0.9999 [0.9999, 1.0000] | 0.1035 [0.0691, 0.1415] | 2.2366 |
| C0 late | 0.9955 [0.9930, 0.9975] | 0.9777 [0.9518, 0.9979] | 0.3343 [0.2194, 0.4558] | 0.8762 |
| C1 early | 0.9997 [0.9996, 0.9998] | 1.0000 [1.0000, 1.0000] | 0.9998 [0.9998, 0.9999] | 0.0028 |
| C1 late | 0.9999 [0.9999, 0.9999] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.0006 |
| C6 early | 0.9998 [0.9998, 0.9998] | 0.9999 [0.9999, 1.0000] | 0.1035 [0.0691, 0.1415] | 2.2366 |
| C6 late | 0.9986 [0.9983, 0.9989] | 0.9997 [0.9997, 0.9998] | 0.1082 [0.0708, 0.1513] | 2.2436 |

Mean conditional probability by **list position** under C0 — the F6
statistic, measured where position is not the answer:

| position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean p | 0.047 | 0.155 | 0.128 | 0.092 | 0.100 | 0.074 | 0.116 | 0.086 | 0.118 | 0.084 |

Edge (first and last) 0.065 against interior 0.109, a ratio of 0.60. Compare the same ratio in `RESULTS.md`, computed on the index arm of this run.

## qwen36_27b

States: 240

**Sensitivity (C1 recovery over values): 160/160 — PASS.** Without this, nothing else on this page is interpretable.

| Condition | answers with a number | of that, an offered value | mass on the consistent value | entropy (bits) |
|---|---|---|---|---|
| C0 early | 0.9984 [0.9982, 0.9985] | 0.9934 [0.9902, 0.9956] | 0.0926 [0.0574, 0.1326] | 2.3346 |
| C0 late | 0.9969 [0.9962, 0.9975] | 0.9939 [0.9868, 0.9980] | 0.3424 [0.2139, 0.4751] | 0.8913 |
| C1 early | 0.9996 [0.9995, 0.9997] | 0.9989 [0.9985, 0.9992] | 0.9975 [0.9965, 0.9983] | 0.0295 |
| C1 late | 0.9999 [0.9998, 0.9999] | 0.9995 [0.9993, 0.9997] | 0.9988 [0.9983, 0.9993] | 0.0147 |
| C6 early | 0.9984 [0.9982, 0.9985] | 0.9934 [0.9902, 0.9956] | 0.0926 [0.0574, 0.1326] | 2.3346 |
| C6 late | 0.9988 [0.9986, 0.9989] | 0.9964 [0.9952, 0.9974] | 0.0991 [0.0589, 0.1452] | 2.2339 |

Mean conditional probability by **list position** under C0 — the F6
statistic, measured where position is not the answer:

| position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean p | 0.126 | 0.184 | 0.166 | 0.136 | 0.082 | 0.058 | 0.098 | 0.048 | 0.076 | 0.026 |

Edge (first and last) 0.076 against interior 0.106, a ratio of 0.72. Compare the same ratio in `RESULTS.md`, computed on the index arm of this run.
