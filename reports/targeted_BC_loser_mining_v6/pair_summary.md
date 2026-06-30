# Targeted B/C Loser Mining v6 Pair Summary

Current Status: BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS

- Smoke rollout: PASS for M0, B, and C.
- Available-condition rollout: PARTIAL_PASS, 5 runnable prefix5 conditions found instead of requested 8/32.
- Generated available5 videos: 15 (5 conditions x 3 models).
- C medium-hard visual candidates: 4 / 5.
- DPO-ready GT>C pairs constructed: 4.
- Required threshold for next DPO smoke: >= 10 pairs; not met.
- 32-condition rollout: NOT_RUN because only 5 runnable prefix5 conditions were present in the current tree.

Decision: Do not run DPO smoke yet. Need more runnable prefix5 conditions or an external/expanded rollout source to reach >=10 clean medium-hard TypeB-C pairs.

## Test Status

- `python -m compileall cam_physgeo src tests`: PASS.
- `pytest -q tests/test_pair_schema_v2v5.py tests/test_medium_hard_loser_selection.py tests/test_reward_guided_pair_selector.py`: NOT_RUN because pytest is unavailable in PATH on the remote host; recorded in `reports/targeted_BC_loser_mining_v6/pytest_v6.log`.
