# Overnight Pipeline Status

Updated: 2026-06-25 02:17:26 CST
Supervisor root: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test`
State file: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test/pipeline_state.json`
Heartbeat log: `local_assets/overnight_quant_lora_dpo_20260624_overnight_test/supervisor.log`

## Status

- sweep_A: RUNNING
- sweep_B: RUNNING
- sweep_C: PASS
- sweep_D: PASS
- rollout_screen: PASS
- video_audit_screen: RUNNING
- quant_screen: PENDING
- reward_calibration: PASS
- candidate_selection: PENDING
- full_benchmark: PENDING
- pair_build: PENDING
- dpo_bf16_single: BLOCKED
- dpo_bf16_ddp2: BLOCKED
- dpo_bf16_ddp8: BLOCKED
- dpo_probe: BLOCKED
- post_dpo_eval: BLOCKED
- git_status: PASS

## GPU / Disk

- free GPUs under 20GiB used: `[4, 5, 6, 7]`
- /home/nvme04 free GB: `338.2`

## Sweep Progress

- A: status=RUNNING step=120/200 gate=PASS fixed_val={'step': 100, 'loss': 0.125425, 'unweighted': 0.185939, 'best': 0.125036, 'finite': 'True'} gpus=0,1
- B: status=RUNNING step=120/200 gate=PASS fixed_val={'step': 100, 'loss': 0.125365, 'unweighted': 0.185848, 'best': 0.125283, 'finite': 'True'} gpus=2,3
- C: status=PASS step=200/200 gate=PASS fixed_val={'step': 200, 'loss': 0.125554, 'unweighted': 0.186221, 'best': 0.125554, 'finite': 'True'} gpus=4,5
- D: status=PASS step=200/200 gate=PASS fixed_val={'step': 200, 'loss': 0.125553, 'unweighted': 0.18622, 'best': 0.125553, 'finite': 'True'} gpus=6,7

## Blockers

- dpo: anchored DPO trainer is still skeleton/guarded; real LingBot-Fast DPO path not callable
- old_tiny_camera: legacy checkpoint lacks adapter_metadata.json required by strict Fast adapter loader

## Safety

- No full-data long StageA launched by this supervisor.
- No StageB / GRPO / large-scale DPO launched.
- No data, videos, HDF5, NPY, checkpoints, adapters, or weights are committed by this supervisor.
