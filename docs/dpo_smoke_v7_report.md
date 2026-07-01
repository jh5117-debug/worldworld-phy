Current Status:
MIXED

# DPO Smoke v7 Report

Tiny SDPO-anchor smoke completed after schema-fixing the reviewed GT>C subset manifest. Runtime status is PASS, but objective signal is not healthy enough to scale.

## Run
- Run dir: `reports/dpo_smoke_v7/sdpo_anchor_gtc10_schemafix_20260701_161657`
- Pair manifest: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Pair count: 10 reviewed GT>C medium-hard pairs
- GPU: physical GPU6 only (`CUDA_VISIBLE_DEVICES=6`)
- Objective: SDPO-anchor / winner-preserving
- Steps: 20
- Trainable params: 6553600
- Status: PASS
- Save/load OK: True
- Nonzero grad: True

## Training Signal
- Final DPO loss: 0.6931381225585938
- Final objective loss: 0.7252156734466553
- Final winner improvement: -0.00026266276836395264
- Final loser degradation: 0.00044423341751098633
- Final winner contribution ratio: 0.0
- Mean winner improvement: 0.00003341
- Mean loser degradation: 0.00019344
- Mean winner contribution ratio: 0.341162

Decision: `ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL`. The chain runs, but final winner improvement is negative and final winner contribution ratio is 0.0, so this should not be scaled.

## Checkpoint Video Eval
- Summary CSV: `reports/dpo_smoke_v7/checkpoint_eval_summary.csv`
- Visual audit: `reports/dpo_smoke_v7/video_audit.csv`
- Contact sheets are in `local_assets/dpo_smoke_v7/checkpoint_video_eval/` and are not tracked by Git.

Visual conclusion: all checkpoints remain readable, but generated futures hallucinate extra balls/fragments. Step010 has the best PSNR/SSIM in this one-sample smoke, while step020 visually and metrically degrades.

## Blocked Metrics
- FVD: `BLOCKED_BY_ENV` (no local real video FVD/I3D backend weights)
- VBench: `BLOCKED_BY_ENV` (`vbench` import unavailable)
- PhysGeo checkpoint reward: `BLOCKED_NOT_RUN_IN_CHECKPOINT_VIDEO_SMOKE`; not fabricated.

## Not Run
No large-scale DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA.
