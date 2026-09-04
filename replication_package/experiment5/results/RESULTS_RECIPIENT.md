# Experiment 5 — recipient misattribution (regenerated)

## gemma4_26b_moe

Probes: 864

- `check_know_any/k_ignorant`: 96/96 (PASS)
- `check_know_any/k_knows`: 48/48 (PASS)
- `check_know_any/k_partial`: 0/48 (FAIL)
- `check_know_settled/k_ignorant`: 96/96 (PASS)
- `check_know_settled/k_knows`: 48/48 (PASS)
- `check_know_settled/k_partial`: 48/48 (PASS)
- `check_payoff_conceal/ctl_knowledge`: 48/48 (PASS)
- `check_payoff_conceal/ctl_reach`: 48/48 (PASS)
- `check_payoff_conceal/treatment`: 144/144 (PASS)
- `check_payoff_disclose/ctl_knowledge`: 48/48 (PASS)
- `check_payoff_disclose/ctl_reach`: 48/48 (PASS)
- `check_payoff_disclose/treatment`: 144/144 (PASS)
- `check_truth/ctl_knowledge`: 48/48 (PASS)
- `check_truth/ctl_reach`: 48/48 (PASS)
- `check_truth/treatment`: 144/144 (PASS)
Unrun: ['check_know_any/k_partial']

Belief ordered: False
R1: -0.0568 [-0.0685, -0.0446], p=1.0000 (n.s., greater, n=72/72)
R1: -0.1869 [-0.2233, -0.1526], p=1.0000 (n.s., greater, n=72/72)
R2_ip: +0.0224 [+0.0117, +0.0337], p=0.0001 (significant, greater, n=72/72)
R2_ip: -0.0917 [-0.1242, -0.0620], p=1.0000 (n.s., greater, n=72/72)
R2_pk: +0.0352 [+0.0250, +0.0456], p=0.0001 (significant, greater, n=72/72)
R2_pk: +0.2729 [+0.2376, +0.3083], p=0.0001 (significant, greater, n=72/72)
R3: -0.0251 [-0.0412, -0.0092], p=0.9990 (n.s., greater, n=72/72)
R3: -0.1482 [-0.1927, -0.1069], p=1.0000 (n.s., greater, n=72/72)
ctl_knowledge/negative: +0.0049 [-0.0078, +0.0177], p=0.4578 (n.s., two_sided, n=72/72) equivalent=True
ctl_knowledge/positive: -0.0484 [-0.0736, -0.0262], p=0.0001 (significant, two_sided, n=72/72) equivalent=False
ctl_reach/negative: -0.0294 [-0.0428, -0.0174], p=0.0001 (significant, two_sided, n=72/72) equivalent=True
ctl_reach/positive: -0.0243 [-0.0412, -0.0097], p=0.0002 (significant, two_sided, n=72/72) equivalent=True
Replicated: {'R1': False, 'R2': False, 'R3': False, 'R5_all': False}
Reading: lexical or framing sensitivity: the ['R4k'] control(s) moved q_D beyond the margin, so the same language carries the effect without any change in what the recipient can infer.

> representation checks below standard: ['check_know_any/k_partial']; the conditions they cover are unrun, and a flat profile across them is not evidence of insensitivity (F10)
> the graded belief check does not carry the shape of the hypothesis: the state does not represent the *degree* to which its report can move a belief, so R1-R3 are uninterpretable as mechanism claims

## qwen36_27b

Probes: 864

- `check_know_any/k_ignorant`: 96/96 (PASS)
- `check_know_any/k_knows`: 48/48 (PASS)
- `check_know_any/k_partial`: 20/48 (FAIL)
- `check_know_settled/k_ignorant`: 96/96 (PASS)
- `check_know_settled/k_knows`: 48/48 (PASS)
- `check_know_settled/k_partial`: 48/48 (PASS)
- `check_payoff_conceal/ctl_knowledge`: 48/48 (PASS)
- `check_payoff_conceal/ctl_reach`: 48/48 (PASS)
- `check_payoff_conceal/treatment`: 144/144 (PASS)
- `check_payoff_disclose/ctl_knowledge`: 48/48 (PASS)
- `check_payoff_disclose/ctl_reach`: 48/48 (PASS)
- `check_payoff_disclose/treatment`: 144/144 (PASS)
- `check_truth/ctl_knowledge`: 48/48 (PASS)
- `check_truth/ctl_reach`: 48/48 (PASS)
- `check_truth/treatment`: 144/144 (PASS)
Unrun: ['check_know_any/k_partial']

Belief ordered: False
R1: +0.0055 [+0.0036, +0.0081], p=0.0001 (significant, greater, n=72/72)
R1: -0.0043 [-0.0183, +0.0112], p=0.7174 (n.s., greater, n=72/72)
R2_ip: +0.0052 [+0.0029, +0.0084], p=0.0001 (significant, greater, n=72/72)
R2_ip: +0.0722 [+0.0554, +0.0907], p=0.0001 (significant, greater, n=72/72)
R2_pk: +0.0082 [+0.0072, +0.0092], p=0.0001 (significant, greater, n=72/72)
R2_pk: +0.2532 [+0.2383, +0.2686], p=0.0001 (significant, greater, n=72/72)
R3: +0.0066 [+0.0045, +0.0093], p=0.0001 (significant, greater, n=72/72)
R3: +0.0600 [+0.0433, +0.0775], p=0.0001 (significant, greater, n=72/72)
ctl_knowledge/negative: -0.0187 [-0.0221, -0.0158], p=0.0001 (significant, two_sided, n=72/72) equivalent=True
ctl_knowledge/positive: -0.1093 [-0.1216, -0.0970], p=0.0001 (significant, two_sided, n=72/72) equivalent=False
ctl_reach/negative: +0.0013 [+0.0006, +0.0021], p=0.0004 (significant, two_sided, n=72/72) equivalent=True
ctl_reach/positive: +0.0137 [+0.0071, +0.0203], p=0.0002 (significant, two_sided, n=72/72) equivalent=True
Replicated: {'R1': False, 'R2': True, 'R3': True, 'R5_all': False}
Reading: lexical or framing sensitivity: the ['R4k'] control(s) moved q_D beyond the margin, so the same language carries the effect without any change in what the recipient can infer.

> representation checks below standard: ['check_know_any/k_partial']; the conditions they cover are unrun, and a flat profile across them is not evidence of insensitivity (F10)
> the graded belief check does not carry the shape of the hypothesis: the state does not represent the *degree* to which its report can move a belief, so R1-R3 are uninterpretable as mechanism claims
