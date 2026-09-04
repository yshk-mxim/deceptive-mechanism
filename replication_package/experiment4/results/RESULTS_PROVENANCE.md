# Experiment 4 — provenance misattribution (regenerated)

## gemma4_26b_moe

Probes: 1727

- `check_circumstance/4A1`: 48/48 (PASS)
- `check_circumstance/4A2`: 48/48 (PASS)
- `check_circumstance/4E`: 0/48 (FAIL)
- `check_objective/4A1`: 48/48 (PASS)
- `check_objective/4A2`: 48/48 (PASS)
- `check_objective/4E`: 48/48 (PASS)
- `check_strategy/4A1`: 48/48 (PASS)
- `check_strategy/4A2`: 48/48 (PASS)
- `check_strategy/4E`: 48/48 (PASS)

derivation/direct: +0.4774 [+0.4616, +0.4941], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning: +0.4418 [+0.3980, +0.4782], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning_rerendered: +0.4536 [+0.4150, +0.4854], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning_truncated: +0.3561 [+0.3115, +0.3989], p=0.0001 (significant, two_sided, n=144/144)
context/direct: +0.0240 [+0.0091, +0.0387], p=0.0007 (significant, greater, n=144/144)
context/reasoning: +0.4846 [+0.4540, +0.5155], p=0.0001 (significant, greater, n=144/144)
context/reasoning_rerendered: +0.4649 [+0.4245, +0.5049], p=0.0001 (significant, greater, n=144/144)
context/reasoning_truncated: +0.3249 [+0.2719, +0.3753], p=0.0001 (significant, greater, n=144/143)
regime/4A1/reasoning: +0.2946 [+0.2541, +0.3300], p=0.0001 (significant, two_sided, n=144/48)
regime/4A1/reasoning_rerendered: +0.3044 [+0.2702, +0.3352], p=0.0001 (significant, two_sided, n=144/48)
regime/4A1/reasoning_truncated: +0.1740 [+0.1304, +0.2186], p=0.0001 (significant, two_sided, n=144/48)
regime/4A2/reasoning: +0.1601 [+0.1162, +0.2076], p=0.0001 (significant, two_sided, n=144/48)
regime/4A2/reasoning_rerendered: +0.1581 [+0.1120, +0.2078], p=0.0001 (significant, two_sided, n=144/48)
regime/4A2/reasoning_truncated: +0.1253 [+0.0756, +0.1746], p=0.0001 (significant, two_sided, n=144/48)
regime/4E/reasoning: -0.3465 [-0.3814, -0.3094], p=0.0001 (significant, two_sided, n=144/48)
regime/4E/reasoning_rerendered: -0.3287 [-0.3654, -0.2877], p=0.0001 (significant, two_sided, n=144/48)
regime/4E/reasoning_truncated: -0.2215 [-0.2726, -0.1637], p=0.0001 (significant, two_sided, n=143/48)
Reading: the tactic is not derived under any regime collected: supplying the objective and the circumstances did not reproduce what stating the strategy achieves [direct: not derived, reasoning: not derived, reasoning_rerendered: not derived, reasoning_truncated: not derived]

> check_circumstance fails in 4E by construction: it asks about the world where its siblings ask what the conversation supplied, and the model correctly infers that an unapproved insider trade would be unwound. Reported, never gating
> 373/432 trajectories state the answer before it is scored, so the regime contrast largely measures self-consistency; the clean subset is too small to substitute for it

## qwen36_27b

Probes: 1689

- `check_circumstance/4A1`: 48/48 (PASS)
- `check_circumstance/4A2`: 48/48 (PASS)
- `check_circumstance/4E`: 36/48 (FAIL)
- `check_objective/4A1`: 48/48 (PASS)
- `check_objective/4A2`: 48/48 (PASS)
- `check_objective/4E`: 48/48 (PASS)
- `check_strategy/4A1`: 48/48 (PASS)
- `check_strategy/4A2`: 48/48 (PASS)
- `check_strategy/4E`: 48/48 (PASS)

derivation/direct: +0.2441 [+0.2279, +0.2604], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning: +0.4275 [+0.3863, +0.4674], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning_rerendered: +0.4063 [+0.3722, +0.4381], p=0.0001 (significant, two_sided, n=144/144)
derivation/reasoning_truncated: +0.2937 [+0.2329, +0.3528], p=0.0001 (significant, two_sided, n=136/130)
context/direct: +0.1896 [+0.1780, +0.2018], p=0.0001 (significant, greater, n=144/144)
context/reasoning: +0.2485 [+0.2026, +0.2962], p=0.0001 (significant, greater, n=144/144)
context/reasoning_rerendered: +0.2781 [+0.2396, +0.3186], p=0.0001 (significant, greater, n=144/144)
context/reasoning_truncated: +0.2615 [+0.2015, +0.3171], p=0.0001 (significant, greater, n=130/127)
regime/4A1/reasoning: +0.3691 [+0.3314, +0.4024], p=0.0001 (significant, two_sided, n=144/48)
regime/4A1/reasoning_rerendered: +0.3815 [+0.3422, +0.4172], p=0.0001 (significant, two_sided, n=144/48)
regime/4A1/reasoning_truncated: +0.2036 [+0.1498, +0.2554], p=0.0001 (significant, two_sided, n=136/48)
regime/4A2/reasoning: -0.0172 [-0.0485, +0.0122], p=0.2728 (n.s., two_sided, n=144/48)
regime/4A2/reasoning_rerendered: +0.0164 [-0.0056, +0.0350], p=0.1302 (n.s., two_sided, n=144/48)
regime/4A2/reasoning_truncated: -0.0489 [-0.0860, -0.0170], p=0.0018 (significant, two_sided, n=130/48)
regime/4E/reasoning: -0.1182 [-0.1593, -0.0762], p=0.0001 (significant, two_sided, n=144/48)
regime/4E/reasoning_rerendered: -0.1142 [-0.1530, -0.0754], p=0.0001 (significant, two_sided, n=144/48)
regime/4E/reasoning_truncated: -0.1629 [-0.1999, -0.1243], p=0.0001 (significant, two_sided, n=127/48)
Reading: the tactic is not derived under any regime collected: supplying the objective and the circumstances did not reproduce what stating the strategy achieves [direct: not derived, reasoning: not derived, reasoning_rerendered: not derived, reasoning_truncated: not derived]

> check_circumstance fails in 4E by construction: it asks about the world where its siblings ask what the conversation supplied, and the model correctly infers that an unapproved insider trade would be unwound. Reported, never gating
> 378/432 trajectories state the answer before it is scored, so the regime contrast largely measures self-consistency; the clean subset is too small to substitute for it
