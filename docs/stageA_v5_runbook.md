# StageA v5 Broad-LoRA Runbook

## 1. Protect TDW Generation

Before any StageA command:

```bash
tmux ls | grep -E 'tdw_v5_4000_gpu0_scaleup|tdw_v5_4000_monitor'
nvidia-smi pmon -c 1
```

Do not attach to, kill, restart, or send keys to TDW tmux sessions. Do not include GPU0 in `CUDA_VISIBLE_DEVICES`.

## 2. Prepare Stage1 Dataset From Converted Manifest

The Stage1 trainer expects CSV + clip directories. Prepare a dataset from converted LingBot manifests:

```bash
python -m cam_physgeo.data.prepare_stage1_dataset_from_lingbot_manifest \
  --train_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/train.jsonl \
  --val_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/val.jsonl \
  --test_manifest local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/test.jsonl \
  --project_root /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work \
  --out_dir local_assets/experiments/exp_stageA_v5_broad_lora/stage1_dataset \
  --link_mode hardlink
```

## 3. Snapshot generated_v5 Progress

This does not make generated_v5 trainable; it records validation state.

```bash
python -m cam_physgeo.data.build_stageA_v5_snapshot \
  --generated_root /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/data/physion/generated_v5 \
  --manifest_chunks_dir /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/data/physion/generated_v5/manifests/v5_scaleup_4000_chunks \
  --reports_dir /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/data/physion/generated_v5/reports \
  --out_dir local_assets/experiments/exp_stageA_v5_broad_lora/manifests
```

If validation status is `blocked`, do not launch formal generated_v5 training.

## 4. Dry Run Launcher

```bash
CUDA_VISIBLE_DEVICES=7 scripts/launch_stageA_v5_broad_lora.sh --dry-run \
  --dataset_dir local_assets/experiments/exp_stageA_v5_broad_lora/stage1_dataset
```

## 5. Preflight

```bash
CUDA_VISIBLE_DEVICES=7 scripts/launch_stageA_v5_broad_lora.sh --preflight \
  --dataset_dir local_assets/experiments/exp_stageA_v5_broad_lora/stage1_dataset \
  --output_root local_assets/experiments/exp_stageA_v5_broad_lora/preflight \
  --max_train_optimizer_steps 12 \
  --branch_mode low
```

## 6. Formal Run

Only after data validation passes:

```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 scripts/launch_stageA_v5_broad_lora.sh --run \
  --dataset_dir local_assets/experiments/exp_stageA_v5_broad_lora/stage1_dataset \
  --output_root local_assets/experiments/exp_stageA_v5_broad_lora/train \
  --nproc_per_node 4 \
  --branch_mode sequence
```

## 7. Output Expectations

Each branch checkpoint stores:

- merged eval-compatible `diffusion_pytorch_model.bin`
- adapter-only `adapter_state.pt`
- `adapter_metadata.json`

Do not commit local_assets or checkpoint files.
