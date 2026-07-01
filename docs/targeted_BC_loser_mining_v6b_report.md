# Targeted B/C Loser Mining v6b Report

Current Status: READY_FOR_TINY_DPO_SMOKE

Updated: 2026-07-01 09:20:29 CST

## Why v6 only had 5 runnable conditions

v6 only consumed already-materialized DPO prefix5 condition directories. The quant benchmark manifests had valid full videos, poses, intrinsics, prompts, and images, but prefix/future MP4 files were not materialized for the V2V-5 runner. v6b recovered those rows by cutting prefix frames 0-4 and GT future frames 5-80 from existing full videos.

## Recovered conditions

- Recovered manifest: `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`
- Runnable count: 32 / 32
- Template balance: 8 drop, 8 collision, 8 roll, 8 containment
- Condition check: `reports/targeted_BC_loser_mining_v6b/runnable_condition_check.csv`

## Rollout status

- Smoke: PASS for M0, B, and C.
- 16-condition rollout: PASS for M0, B, and C.
- 32-condition rollout: PASS for B and C. M0 baseline is PARTIAL for 32cond (first16 only); it was not required for GT>C pair construction.
- B videos: 32 / 32 available across first16 + remaining16.
- C videos: 32 / 32 available across first16 + remaining16.

## Metrics

- Metrics table: `reports/targeted_BC_loser_mining_v6b/metric_summary_32cond.csv`
- Model/template summary: `reports/targeted_BC_loser_mining_v6b/metric_model_template_summary_32cond.csv`
- Reward vectors: `reports/targeted_BC_loser_mining_v6b/reward_vectors_32cond.jsonl`
- PSNR/SSIM/sharpness/freeze/diagnostic reward proxies were computed.
- LPIPS/FVD/VBench remain `BLOCKED_BY_ENV` where local backends/assets are unavailable; no metric was fabricated.

## Codex visual audit

Codex inspected overview contact sheets for first16 and remaining16 conditions. C produced readable medium-hard candidates, especially in drop, roll, containment, and selected collision cases. B remained the cleaner/stabler candidate generator baseline.

- Video audit: `reports/targeted_BC_loser_mining_v6b/video_audit_32cond.csv`
- Medium-hard C loser candidates selected: 16

## Pair construction

Preferred construction: `GT > C`

- Winner: clean GT future
- Loser: C camera+self-temporal rank4 rollout
- DPO-ready GT>C pairs: 15
- Pair audit: `reports/targeted_BC_loser_mining_v6b/pair_candidate_audit.csv`
- DPO-ready pairs: `reports/targeted_BC_loser_mining_v6b/dpo_ready_pairs_v6b.jsonl`
- Final manifest: `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`

Decision: READY_FOR_TINY_DPO_SMOKE in a later round. Do not run large-scale DPO.

## PPT showcase

- MP4: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6b_for_ppt.mp4`
- Selected CSV: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6b_selected.csv`
- Notes: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6b_notes.md`

The MP4 is an output artifact and must not be committed.

## Explicit non-runs

No DPO training, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, checkpoint modification, or data/weights/video push was performed.

## Verification

- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/bin/python -m compileall cam_physgeo src tests`: PASS.
- `pytest`: PYTEST_UNAVAILABLE_IN_PHYS_ENV, so pytest PASS is not claimed.
