# GPU Approval Request: TDW v5 Base vs Stage A Adapter Rollout

Date: 2026-06-10

## Request

Approve a bounded rollout smoke comparing base LingBot-Fast and the balanced Stage A adapter.

## Recommended First Run

- 4 conditions total;
- one each for drop, collision, roll, containment;
- base rollout + Stage A adapter rollout;
- GPU7 preferred, GPU6 fallback;
- no training;
- no DPO;
- no reward calibration;
- output videos only.

## Command Draft

```bash
CUDA_VISIBLE_DEVICES=7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python -m cam_physgeo.eval.rollout_compare_base_adapter \
  --config configs/cam_physgeo/videogpa_adapter.yaml \
  --manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/test.jsonl \
  --adapter_checkpoint local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt \
  --out local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout \
  --num_conditions 4 \
  --templates drop collision roll containment \
  --num_frames 81 \
  --resolution 480x832 \
  --run_base true \
  --run_adapter true \
  --make_contact_sheet true \
  --local_files_only true
```

If the 4-condition run succeeds and runtime is acceptable, expand to 12 conditions.
