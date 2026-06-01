# Current State Before LoRA Optimizer-Step Dry-Run

## Summary

- Previous branch: `physion-dpo-tiny-lora-backward`
- Previous commit: `a1e2800b317545c8dd0ce7cdb326c18903555212`
- This local branch: `physion-dpo-lora-optimizer-step-dryrun`
- Current goal: 1-pair / 1-step optimizer-step dry-run on runtime tiny camera-control LoRA only.

## Previous LoRA Backward Result

- LoRA target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA rank / alpha: `2 / 4.0`
- LoRA trainable params: `40,960`
- Backward-only status: passed
- `L_DPO`: `0.6931474208831787`
- LoRA params with grad: `4`
- Base params with grad: `0`
- Reference params with grad: `0`
- NaN/Inf gradients: no
- Parameter diff after backward-only: `0.0`
- Optimizer step: not run in previous round
- LoRA/checkpoint save: none

## Current Permission Boundary

Allowed:

- one pair only;
- one optimizer step only;
- optimizer param group containing LoRA params only;
- base/reference frozen checks;
- param diff summaries under `local_assets/outputs/smoke`.

Not allowed:

- formal training;
- VideoGPA `03_train.py`;
- multi-pair DPO;
- rollout generation;
- reward calibration;
- TDW/Physion generation;
- checkpoint save;
- LoRA save;
- updates to original LingBot weights.

## Gate Status

- Gate A: passed, LingBot-Fast 1-sample inference.
- Gate B: passed, 3 Fast rollouts.
- Gate C: partial/pass, camera embedding and strong stress effect passed; ordinary frozen/correct remains weak.
- Gate D: partial/pass, reward v5 ordering and real RAFT/DINO smoke passed but not full DPO-ready.
- Gate E: optimizer-step dry-run pending.
- Gate F: real DPO training still no.
