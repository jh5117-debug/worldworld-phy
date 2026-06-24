# Overnight Pipeline Status

Updated: 2026-06-24 17:28:08 CST
Supervisor root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/overnight_quant_lora_dpo_20260624_overnight_test`
State file: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/overnight_quant_lora_dpo_20260624_overnight_test/pipeline_state.json`
Heartbeat log: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/local_assets/overnight_quant_lora_dpo_20260624_overnight_test/supervisor.log`

## Status

- sweep_A: RUNNING
- sweep_B: RUNNING
- sweep_C: RUNNING
- sweep_D: RUNNING
- rollout_screen: PENDING
- video_audit_screen: PENDING
- quant_screen: PENDING
- reward_calibration: RUNNING
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

- free GPUs under 20GiB used: `[]`
- /home/nvme04 free GB: `340.24`

## Sweep Progress

- A: status=RUNNING step=31/200 gate=WAIT fixed_val=None gpus=0,1
- B: status=RUNNING step=31/200 gate=WAIT fixed_val=None gpus=2,3
- C: status=RUNNING step=70/200 gate=PASS fixed_val={'step': 50, 'loss': 0.125559, 'unweighted': 0.186228, 'best': 0.125559, 'finite': 'True'} gpus=4,5
- D: status=RUNNING step=72/200 gate=PASS fixed_val={'step': 50, 'loss': 0.125559, 'unweighted': 0.186227, 'best': 0.125559, 'finite': 'True'} gpus=6,7

## Blockers

- dpo: anchored DPO trainer is still skeleton/guarded; real LingBot-Fast DPO path not callable
- old_tiny_camera: legacy checkpoint lacks adapter_metadata.json required by strict Fast adapter loader

## Safety

- No full-data long StageA launched by this supervisor.
- No StageB / GRPO / large-scale DPO launched.
- No data, videos, HDF5, NPY, checkpoints, adapters, or weights are committed by this supervisor.
