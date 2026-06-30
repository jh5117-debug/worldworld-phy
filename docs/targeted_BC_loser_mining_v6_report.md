# Targeted B/C Small-LoRA Loser Mining v6 Report

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

## Summary

The v6 PRD was prepared and pushed before execution. B/C checkpoints were successfully located and fingerprinted, but new targeted rollout was not started because the machine was not in a safe rollout state: all GPUs had high memory occupancy in the initial status check, and subsequent compute-app `nvidia-smi` queries hung. Repository runner discovery also timed out under the current filesystem/I/O conditions.

No DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or checkpoint modification was performed.

## Checkpoint Inventory

- B_camera_r8: step 200, rank 8, groups camera_conditioning, trainable params 13107200, adapter `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_B_camera_r8_train200_20260624_141215/checkpoints/small_lora_B_camera_r8_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter/adapter_state.pt`, sha256 `24016fc189fe4954...`
- C_camera_self_temporal_r4: step 200, rank 4, groups camera_conditioning;self_attention, trainable params 1310720, adapter `local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000200/fast_stageA_high_noise_adapter/adapter_state.pt`, sha256 `757a1854e3bc6756...`

## Rollout Status

- Conditions selected: 0
- New rollout videos generated: 0
- New contact sheets generated: 0
- Metrics computed on new videos: 0
- Codex visual audit on new videos: blocked, no new videos

## Medium-Hard Loser Mining Result

- Medium-hard loser count: 0
- DPO-ready pair count: 0
- Final pair manifest: `manifests/dpo_typeB_C_loser_pairs_v6.jsonl` (empty)
- DPO-ready manifest: `reports/targeted_BC_loser_mining_v6/dpo_ready_pairs_v6.jsonl` (empty)

## Decision

B remains the best candidate generator / control baseline. C remains the best scoped candidate for future medium-hard loser mining. However, v6 cannot claim that C produced medium-hard losers because no new rollout was safely run. Do not proceed to DPO smoke from this v6 state.

## Next Action

Resume v6 when a safe GPU slot is available and the rollout runner path is confirmed. Start with 32 locked conditions, M0/M_B/M_C, seeds=2, then compute PSNR/SSIM/LPIPS, PhysGeo rewards, sharpness/blur/freeze, and Codex visual audit before pair construction.

## Verification

- `python3 -m compileall cam_physgeo src tests`: PASS.
- `pytest -q tests/test_pair_schema_v2v5.py tests/test_medium_hard_loser_selection.py tests/test_reward_guided_pair_selector.py`: BLOCKED_BY_ENV, `pytest` command not found in the active remote shell. No pytest PASS was claimed.
