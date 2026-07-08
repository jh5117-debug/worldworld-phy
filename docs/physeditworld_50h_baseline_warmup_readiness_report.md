# PhysEditWorld 50h Baseline And Warm-Up Readiness Report

Updated: 2026-07-08T18:44:19 CST

## Decision

`PHASE3_PHASE4_SCAFFOLD_READY_DATA_BLOCKED`

## What Is Ready

- Offline gravity metric helpers: `cam_physgeo/eval/gravity_metrics.py`.
- Baseline rollout gate wrapper: `cam_physgeo/eval/physeditworld_baseline_rollout.py`.
- Rank32 warm-up config: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`.
- Future ablation plan: `docs/experiments/EXP_physeditworld50_plus_ourphysics50_ablation_plan.md`.

## Gate Result

The current LingBot converted train manifest is empty:

- `manifests/physeditworld_50h_lingbot_train.jsonl`: 0 rows.
- Baseline rollout wrapper result: `BASELINE_BLOCKED_EMPTY_MANIFEST`.
- No Original Fast / LingBot-Base rollout was launched.
- No support warm-up was launched.
- No GPU was used for this smoke.

## Smoke Evidence

- Compile log: `reports/physeditworld_50h/test_logs/compileall_phase3_phase4.log`.
- Direct smoke log: `reports/physeditworld_50h/test_logs/direct_phase3_phase4_smoke.log`.
- Baseline summary: `reports/physeditworld_50h_baseline_rollout/summary.md`.
- Gravity metric smoke: `reports/physeditworld_50h/gravity_metrics/gravity_smoke_summary.md`.
- Pytest status: `PYTEST_UNAVAILABLE` in `reports/physeditworld_50h/test_logs/pytest_phase3_phase4.log`; no pytest PASS is claimed.

## Warm-Up Config Summary

- Model line: LingBot-Fast.
- Data line: PhysEditWorld 50h only.
- Gravity conditioning: prompt-only.
- LoRA: rank32 first.
- Precision: BF16 mixed-safe with VAE FP32 and camera/action/intrinsics FP32.
- GPU policy: physical GPU4,5,6,7 only; GPU0,1,2,3 forbidden.
- Gate checkpoints: step0, step500, step1000, step2000.
- No StageB, GRPO, broad-LoRA, large DPO, train400, or full-data long StageA.

## Blocker

The actual selected PhysEditWorld 50h root is still not visible on H20. Until a strict manifest has nonzero rows with action, camera, intrinsics, gravity, and video paths, Phase 3 true rollout and Phase 4 warm-up remain blocked.

## Explicit Non-Runs

- No training.
- No rollout.
- No DPO.
- No StageA/StageB/GRPO.
- No checkpoint deletion.
- No videos/images/checkpoints/weights pushed.
