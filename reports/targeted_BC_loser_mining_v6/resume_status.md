# Targeted B/C Loser Mining v6 Resume Status

Current Status: BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS

Updated: 2026-06-30 20:50:46 CST

Previous blocker was GPU query and runner discovery hanging. This round fixed both by adding `scripts/safe_gpu_status.sh` and using deterministic `cam_physgeo.eval.run_v2v5_inference`. Smoke rollout passed for M0/B/C. Available-condition rollout produced 15 videos from the 5 runnable prefix5 conditions currently present. C produced 4 medium-hard visual candidates, but the >=10 DPO-smoke pair gate was not met. No DPO training was run.
