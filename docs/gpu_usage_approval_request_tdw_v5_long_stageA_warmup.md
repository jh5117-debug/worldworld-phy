# GPU Approval Request: Longer TDW v5 Stage A Warmup

Date: 2026-06-10

## Request

Approve a longer Stage A high-noise warmup only if the user wants to spend the runtime before rollout inspection.

## Runtime Estimate

The 60-step balanced Stage A pilot took about 9028 seconds. A 300-step run is expected to exceed 12 hours.

## Proposed Command Shape

- GPU: GPU7 or GPU6/7
- dataset: TDW v5 200 train/val split
- steps: 300
- batch size: 1
- timestep mode: high-noise diagnostic
- trainable scope: `camera_control_lora_tiny`
- checkpoint: adapter-only final checkpoint
- no full model checkpoint
- no optimizer state
- no DPO
- no rollout during training

Explicit approval is required before execution.
