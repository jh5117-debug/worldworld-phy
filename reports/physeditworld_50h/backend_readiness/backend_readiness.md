# PhysEditWorld LingBot Backend Readiness

Decision: `PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY`

## Status Counts

- `BLOCKED`: 3
- `PASS`: 16

## Checks

- `lingbot_code_link`: `PASS`
  - evidence: `links/lingbot_code`
  - detail: exists; symlink_target=/home/nvme03/workspace/world_model_phys/code/lingbot-world
- `base_model_link`: `PASS`
  - evidence: `links/base_model`
  - detail: exists; symlink_target=/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam
- `weights_manifest`: `PASS`
  - evidence: `reports/migration/required_weights_manifest.tsv`
  - detail: exists
- `data_manifest`: `PASS`
  - evidence: `reports/migration/required_data_manifest.tsv`
  - detail: exists
- `warmup_config_exists`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: exists
- `warmup_config_prompt_only_gravity`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: gravity_prompt_only=True
- `warmup_config_lora_rank32`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: lora_rank=32
- `warmup_config_gpu_policy`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: allowed_gpus=True forbidden_gpus=True
- `weights_manifest_lingbot_code`: `PASS`
  - evidence: `reports/migration/required_weights_manifest.tsv`
  - detail: tokens=links/lingbot_code,lingbot_code found_existing=True
- `weights_manifest_base_model`: `PASS`
  - evidence: `reports/migration/required_weights_manifest.tsv`
  - detail: tokens=links/base_model,lingbot-base,lingbot-fast found_existing=True
- `import_cam_physgeo.eval.physeditworld_baseline_rollout`: `PASS`
  - evidence: `cam_physgeo.eval.physeditworld_baseline_rollout`
  - detail: /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/cam_physgeo/eval/physeditworld_baseline_rollout.py
- `import_cam_physgeo.eval.physeditworld_checkpoint_eval`: `PASS`
  - evidence: `cam_physgeo.eval.physeditworld_checkpoint_eval`
  - detail: /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/cam_physgeo/eval/physeditworld_checkpoint_eval.py
- `import_cam_physgeo.training.train_physeditworld_warmup`: `PASS`
  - evidence: `cam_physgeo.training.train_physeditworld_warmup`
  - detail: /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/cam_physgeo/training/train_physeditworld_warmup.py
- `import_cam_physgeo.dpo.physeditworld_pair_manifest_validate`: `PASS`
  - evidence: `cam_physgeo.dpo.physeditworld_pair_manifest_validate`
  - detail: /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/cam_physgeo/dpo/physeditworld_pair_manifest_validate.py
- `baseline_rollout_backend_connected`: `BLOCKED`
  - evidence: `cam_physgeo/eval/physeditworld_baseline_rollout.py`
  - detail: found marker BASELINE_BACKEND_NOT_CONNECTED
  - next: wire real LingBot-Fast V2V-5 baseline rollout invocation with no image-only fallback
- `checkpoint_eval_backend_connected`: `BLOCKED`
  - evidence: `cam_physgeo/eval/physeditworld_checkpoint_eval.py`
  - detail: found marker CHECKPOINT_EVAL_BACKEND_NOT_CONNECTED
  - next: wire real checkpoint rollout, metrics, and Codex visual audit runner
- `warmup_training_backend_connected`: `BLOCKED`
  - evidence: `cam_physgeo/training/train_physeditworld_warmup.py`
  - detail: found marker WARMUP_BACKEND_NOT_CONNECTED
  - next: connect gated LingBot-Fast rank32 warm-up backend after manifest validation
- `torch_import`: `PASS`
  - evidence: `torch`
  - detail: torch=2.7.1+cu128 cuda_available=True
- `python_version`: `PASS`
  - evidence: `/usr/bin/python3`
  - detail: 3.10.6 (main, Aug 10 2022, 11:40:04) [GCC 11.3.0]

## Safety

This audit is CPU/IO only. It imports lightweight Python modules and reads manifests/configs; it does not load model weights, use GPUs, train, rollout, copy, delete, or push local_assets.
