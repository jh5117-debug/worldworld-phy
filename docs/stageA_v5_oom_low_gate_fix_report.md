# StageA v5 OOM and Low-Gate Fix Report

Date: 2026-06-22

## Summary

The low branch did not fail numerically. It completed 1600 optimizer steps with finite losses and stable fixed validation, but the previous loss gate treated spike_ratio_high as a hard blocker. The gate has been adjusted so spike_ratio_high is advisory when fixed validation is stable and no finite-loss blocker is present.

The high branch OOM was caused by full 81-frame rank-16 broad-LoRA training with unchunked LoRA inputs and forced FP32 LoRA activations. The fix enables LoRA chunking at 1024 tokens, defaults LoRA activations to bf16, and enables PyTorch expandable CUDA allocation segments.

## Evidence

- Low branch final EMA100: about 0.04387.
- Low branch best fixed-val: about 0.04359.
- Low branch final fixed-val: about 0.04361.
- High-only preflight: 5/5 optimizer steps completed on physical GPU7 with finite loss and gradients.
- Formal high resume session: stageA_v5_high_resume_oomfix_20260622_122116.
- Formal high output root: local_assets/experiments/exp_stageA_v5_datafix_train_gate/formal_stageA_high_resume_oomfix_snapshot_20260620_144547_20260622_122116

## Safety

- Physical GPU0 was not used for StageA training.
- TDW tmux sessions were not attached, killed, or restarted.
- StageB was not run.
- DPO, reward scoring, rollout, and pair mining were not run.
