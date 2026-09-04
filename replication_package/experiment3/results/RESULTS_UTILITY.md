# Experiment 3 — utility misattribution (regenerated)

## gemma4_26b_moe

Probes: 1080

- `check_recipient/k_aware`: 90/90 (PASS)
- `check_recipient/k_unaware`: 90/90 (PASS)
- `check_utility_conceal/u_minus`: 44/60 (FAIL)
- `check_utility_conceal/u_plus`: 45/60 (FAIL)
- `check_utility_conceal/u_zero`: 60/60 (PASS)
- `check_utility_disclose/u_minus`: 54/60 (PASS)
- `check_utility_disclose/u_plus`: 59/60 (PASS)
- `check_utility_disclose/u_zero`: 60/60 (PASS)
Unrun: ['u_minus', 'u_plus']

U2: +0.0422 [+0.0328, +0.0506], p=0.0001 (significant, greater, n=180/180)
U3: +0.1996 [+0.1856, +0.2145], p=0.0001 (significant, greater, n=270/270)
U3/u_zero: +0.3349 [+0.3065, +0.3594], p=0.0001 (significant, greater, n=90/90)
U1: -0.3918 [-0.4011, -0.3857], p=1.0000 (n.s., greater, n=540/540)
frame: +0.0850 [+0.0703, +0.0977], p=0.0001 (significant, two_sided, n=270/270)
U2 ordered pattern U+ > U0 > U-: False
U2 established (U7 trigger): False

> manipulation check failed in ['u_minus', 'u_plus']; those conditions are unrun, and a flat profile across them is not evidence of insensitivity (F10)
> checks passing only narrowly: ['check_utility_disclose/u_minus']. A check at its threshold is not the same evidence as one at 1.000, and a tenth of the states not representing the manipulation is a caveat on any contrast computed over them

### gemma4_26b_moe — U7 objective locus

Triggered: False

Reading: not evaluated

> NOT TRIGGERED: U7 is pre-registered but conditional on U2 establishing utility sensitivity, which requires both a positive contrast and payoff conditions that represented the payoff rule

## qwen36_27b

Probes: 1080

- `check_recipient/k_aware`: 90/90 (PASS)
- `check_recipient/k_unaware`: 90/90 (PASS)
- `check_utility_conceal/u_minus`: 28/60 (FAIL)
- `check_utility_conceal/u_plus`: 60/60 (PASS)
- `check_utility_conceal/u_zero`: 60/60 (PASS)
- `check_utility_disclose/u_minus`: 60/60 (PASS)
- `check_utility_disclose/u_plus`: 46/60 (FAIL)
- `check_utility_disclose/u_zero`: 60/60 (PASS)
Unrun: ['u_minus', 'u_plus']

U2: +0.1715 [+0.1619, +0.1818], p=0.0001 (significant, greater, n=180/180)
U3: +0.1200 [+0.1134, +0.1258], p=0.0001 (significant, greater, n=270/270)
U3/u_zero: +0.1327 [+0.1177, +0.1525], p=0.0001 (significant, greater, n=90/90)
U1: -0.6204 [-0.6473, -0.5936], p=1.0000 (n.s., greater, n=540/540)
frame: +0.3039 [+0.2896, +0.3190], p=0.0001 (significant, two_sided, n=270/270)
U2 ordered pattern U+ > U0 > U-: True
U2 established (U7 trigger): False

> manipulation check failed in ['u_minus', 'u_plus']; those conditions are unrun, and a flat profile across them is not evidence of insensitivity (F10)

### qwen36_27b — U7 objective locus

Triggered: False

Reading: not evaluated

> NOT TRIGGERED: U7 is pre-registered but conditional on U2 establishing utility sensitivity, which requires both a positive contrast and payoff conditions that represented the payoff rule

### gemma4_26b_moe — U2 rerun (stage 11)

Probes: 864, instances: 24

- `check_recipient/k_aware`: 72/72 (PASS)
- `check_recipient/k_unaware`: 72/72 (PASS)
- `check_utility_conceal/u_minus`: 48/48 (PASS)
- `check_utility_conceal/u_plus`: 35/48 (FAIL)
- `check_utility_conceal/u_zero`: 48/48 (PASS)
- `check_utility_disclose/u_minus`: 47/48 (PASS)
- `check_utility_disclose/u_plus`: 48/48 (PASS)
- `check_utility_disclose/u_zero`: 48/48 (PASS)
U2: +0.0463 [+0.0395, +0.0536], p=0.0001 (significant, greater, n=288/288)
U0-U+: +0.1358 [+0.1191, +0.1518], p=0.0001 (significant, two_sided, n=288/288)
U0-U-: +0.1821 [+0.1662, +0.1972], p=0.0001 (significant, two_sided, n=288/288)
U3/u_minus: +0.1053 [+0.0972, +0.1139], p=0.0001 (significant, greater, n=144/144)
U3/u_plus: +0.1516 [+0.1382, +0.1648], p=0.0001 (significant, greater, n=144/144)
U3/u_zero: +0.3954 [+0.3621, +0.4270], p=0.0001 (significant, greater, n=144/144)
Ordered U+ > U0 > U-: False
U2 established (U7 trigger): False

> payoff checks below standard at ['u_plus']; the contrasts are computed and reported, and the findings say what that failure means for reading them

### qwen36_27b — U2 rerun (stage 11)

Probes: 864, instances: 24

- `check_recipient/k_aware`: 72/72 (PASS)
- `check_recipient/k_unaware`: 72/72 (PASS)
- `check_utility_conceal/u_minus`: 33/48 (FAIL)
- `check_utility_conceal/u_plus`: 48/48 (PASS)
- `check_utility_conceal/u_zero`: 48/48 (PASS)
- `check_utility_disclose/u_minus`: 48/48 (PASS)
- `check_utility_disclose/u_plus`: 48/48 (PASS)
- `check_utility_disclose/u_zero`: 48/48 (PASS)
U2: +0.1865 [+0.1780, +0.1946], p=0.0001 (significant, greater, n=288/288)
U0-U+: -0.0831 [-0.0890, -0.0768], p=0.0001 (significant, two_sided, n=288/288)
U0-U-: +0.1034 [+0.0982, +0.1085], p=0.0001 (significant, two_sided, n=288/288)
U3/u_minus: +0.0605 [+0.0555, +0.0656], p=0.0001 (significant, greater, n=144/144)
U3/u_plus: +0.1767 [+0.1647, +0.1898], p=0.0001 (significant, greater, n=144/144)
U3/u_zero: +0.1427 [+0.1348, +0.1510], p=0.0001 (significant, greater, n=144/144)
Ordered U+ > U0 > U-: True
U2 established (U7 trigger): False

> payoff checks below standard at ['u_minus']; the contrasts are computed and reported, and the findings say what that failure means for reading them
