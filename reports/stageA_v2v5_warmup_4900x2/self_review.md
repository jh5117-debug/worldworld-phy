# Self Review: StageA V2V-5 Warmup 4900x2

## Checks Performed

- Verified H20-2 repo and branch.
- Verified GPU4-7 were idle and GPU0-3 were occupied by other jobs.
- Counted generated_v5 current disk data:
  - raw HDF5: 3999
  - main converted Stage1-ready dirs: 3299
  - worktree converted Stage1-ready dirs: 368, duplicate subset
  - unique Stage1-ready dirs: 3299
- Rechecked previous pilot warmup:
  - train/val/test = 800/100/100
  - hard max optimizer steps = 100
  - camera-conditioning LoRA rank4
- Created strict 4900/100 builder and launcher.
- Ran builder data gate: BLOCKED_INSUFFICIENT_STAGE1_READY_DATA.
- Ran launcher dry block with timeout: exit 42 before training.

## Validation

- `compileall` passed for the new builder and test file.
- `pytest` did not run because `PYTHONNOUSERSITE=1` excludes user-site `pygments`, while normal site initialization hangs. This is recorded as an environment blocker, not a test pass.

## Decision

No warmup training was launched. The requested 4900 train / 100 test split is not available on disk.

## Next Action

Recover or generate at least 1701 more unique Stage1-ready clips, then rerun:

```bash
PYTHONNOUSERSITE=1 /home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python3.10 \
  cam_physgeo/data/build_v2v5_warmup_4900_split.py \
  --converted_root /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v5/converted_stage1_v1 \
  --dataset_dir local_assets/stageA_v2v5_4900x2/dataset \
  --report_dir reports/stageA_v2v5_warmup_4900x2
```

Then launch:

```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 bash scripts/launch_fast_stageA_v2v5_camera_r4_4900x2.sh
```
