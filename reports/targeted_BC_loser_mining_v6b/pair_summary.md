# Targeted B/C Loser Mining v6b Pair Summary

Current Status: READY_FOR_TINY_DPO_SMOKE

- Recovered runnable prefix5 conditions: 32
- 16-condition rollout: PASS for M0/B/C.
- 32-condition rollout: PASS for B and C; M0 baseline is PARTIAL (first 16 only) and not used for pair construction.
- B camera-r8: stable candidate generator/control baseline.
- C camera+self-temporal-r4: medium-hard loser source.
- Codex visual reviewed overview sheets for first16 and remaining16.
- C medium-hard candidates selected: 16
- DPO-ready GT>C pairs: 15
- Decision: READY_FOR_TINY_DPO_SMOKE if next round runs only a tiny smoke; no DPO was run in v6b.

Failure tags: {'event_extra_objects': 1, 'event_missing_or_fragments': 1, 'physical_event_fragments': 1, 'containment_failure': 3, 'foreground_identity_event': 1, 'foreground_identity_extra_objects': 2, 'collision_event_failure': 1, 'collision_extra_objects': 1, 'roll_identity_event': 2, 'containment_extra_objects': 2}

Blocked/partial items:
- M0 remaining16 rollout was not required for GT>C pair construction and remains partial.
- LPIPS/FVD/VBench remain BLOCKED_BY_ENV in this v6b scoring table where unavailable.
