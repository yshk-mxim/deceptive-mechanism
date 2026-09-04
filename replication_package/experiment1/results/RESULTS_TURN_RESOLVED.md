# Experiment 1 — turn-resolved metrics (Tier 2)

Luo et al.'s **Drift Rate** (`#changes / T`) and **KL** (`D_KL(P_t ‖ P_{t-1})`) as
they define them, over the six-point trajectory `early → turn1 … turn4 → late`,
with the positive control their design lacks: C1 and C2 place a target in the state,
so drift has a measurable floor rather than an assumed one.

`Branch D.R.` is their Appendix C metric, `1(p_T ≠ p_0)` — the quantity the two-point
grid reports elsewhere in this package. It is shown beside the others so the
difference between the proxy and the headline metric is visible rather than argued.

**Tier 2. Tier 1 rests on state identity and does not depend on turn resolution.**

## gemma4_26b_moe

Complete trajectories: 240

| Condition | Drift Rate (#changes/T) | Once D.R. | Branch D.R. |
|---|---|---|---|
| C0 | 0.353 [0.303, 0.403] | 1.000 [1.000, 1.000] | 0.967 [0.900, 1.000] |
| C1 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| C2 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| C4 | 0.377 [0.307, 0.450] | 1.000 [1.000, 1.000] | 0.850 [0.717, 0.967] |

Where the drift happens — fraction of trajectories changing target at
each step, and the mean KL of that step in bits:

| Condition | | early→turn1 | turn1→turn2 | turn2→turn3 | turn3→turn4 | turn4→late |
|---|---|---|---|---|---|---|
| C0 | changed | 0.783 | 0.667 | 0.183 | 0.100 | 0.033 |
| | KL (bits) | 5.37 | 3.66 | 0.17 | 0.06 | 0.03 |
| C1 | changed | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| | KL (bits) | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| C2 | changed | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| | KL (bits) | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| C4 | changed | 0.917 | 0.633 | 0.150 | 0.117 | 0.067 |
| | KL (bits) | 3.82 | 3.71 | 0.12 | 0.09 | 0.03 |
**C4 — is the distractor retained, or merely available?** Mass on
the previous game's index at each probe point, with the
constraint-consistent answer beside it:

| | early | turn1 | turn2 | turn3 | turn4 | late |
|---|---|---|---|---|---|---|
| distractor | 0.0292 | 0.0895 | 0.1410 | 0.1170 | 0.0835 | 0.0845 |
| consistent | 0.0852 | 0.2501 | 0.3645 | 0.3694 | 0.3680 | 0.3617 |

A narrowing step excluded the distractor in 99 of 111 cases: C4 places it outside the consistent set by construction, so a real constraint usually rules it out. Whether its mass then falls is what separates prior mass from a retained belief.

**Does drift track turns, or information?** A filler question is
universally true, so it adds a turn and narrows nothing. Under
"the belief drifts over time" it should drift like any other step.

| Condition | step narrowed the set | step narrowed nothing |
|---|---|---|
| C0 | 0.784 (n=111) | 0.101 (n=189) |
| C1 | 0.000 (n=111) | 0.000 (n=189) |
| C2 | 0.000 (n=111) | 0.000 (n=189) |
| C4 | 0.838 (n=111) | 0.106 (n=189) |

## qwen36_27b

Complete trajectories: 240

| Condition | Drift Rate (#changes/T) | Once D.R. | Branch D.R. |
|---|---|---|---|
| C0 | 0.380 [0.320, 0.443] | 1.000 [1.000, 1.000] | 0.917 [0.783, 1.000] |
| C1 | 0.007 [0.000, 0.020] | 0.017 [0.000, 0.050] | 0.000 [0.000, 0.000] |
| C2 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| C4 | 0.353 [0.293, 0.410] | 0.950 [0.850, 1.000] | 0.950 [0.850, 1.000] |

Where the drift happens — fraction of trajectories changing target at
each step, and the mean KL of that step in bits:

| Condition | | early→turn1 | turn1→turn2 | turn2→turn3 | turn3→turn4 | turn4→late |
|---|---|---|---|---|---|---|
| C0 | changed | 0.900 | 0.667 | 0.133 | 0.167 | 0.033 |
| | KL (bits) | 4.47 | 2.71 | 0.12 | 0.16 | 0.02 |
| C1 | changed | 0.000 | 0.017 | 0.017 | 0.000 | 0.000 |
| | KL (bits) | 0.09 | 0.12 | 0.03 | 0.00 | 0.00 |
| C2 | changed | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| | KL (bits) | 0.14 | 0.08 | 0.02 | 0.00 | 0.01 |
| C4 | changed | 0.950 | 0.533 | 0.150 | 0.067 | 0.067 |
| | KL (bits) | 4.16 | 1.41 | 0.15 | 0.05 | 0.02 |
**C4 — is the distractor retained, or merely available?** Mass on
the previous game's index at each probe point, with the
constraint-consistent answer beside it:

| | early | turn1 | turn2 | turn3 | turn4 | late |
|---|---|---|---|---|---|---|
| distractor | 0.5636 | 0.0996 | 0.1069 | 0.0963 | 0.0892 | 0.0857 |
| consistent | 0.0722 | 0.1710 | 0.3061 | 0.2872 | 0.2985 | 0.2887 |

A narrowing step excluded the distractor in 99 of 111 cases: C4 places it outside the consistent set by construction, so a real constraint usually rules it out. Whether its mass then falls is what separates prior mass from a retained belief.

**Does drift track turns, or information?** A filler question is
universally true, so it adds a turn and narrows nothing. Under
"the belief drifts over time" it should drift like any other step.

| Condition | step narrowed the set | step narrowed nothing |
|---|---|---|
| C0 | 0.838 (n=111) | 0.111 (n=189) |
| C1 | 0.009 (n=111) | 0.005 (n=189) |
| C2 | 0.000 (n=111) | 0.000 (n=189) |
| C4 | 0.775 (n=111) | 0.106 (n=189) |
