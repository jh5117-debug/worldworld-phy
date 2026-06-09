# Codebase / PRD Audit Before True Warmup Forward

Date: 2026-06-09

The repo scan covered `cam_physgeo`, `scripts`, `configs`, and `docs`; the lightweight file list contained 527 Python, shell, YAML, and Markdown files. `local_assets` payload files were not scanned or copied.

## Project Map

| Area | Key Files | Current Role |
|---|---|---|
| TDW generation | `cam_physgeo/data/tdw_generation_v2/*`, `scripts/31_run_tdw_generation_v2_smoke.sh`, `configs/cam_physgeo/tdw_generation_v2.yaml` | Generates Physion-style moving-camera HDF5, validates motion/visibility, converts to LingBot cam-only inputs. |
| Dataset gate | `build_lingbot_dataset_manifest.py`, `audit_lingbot_dataset.py`, `split_lingbot_dataset.py`, `lingbot_dataset_smoke.py` | Builds v5 200 manifest, validates files, splits train/val/test, and checks video/camera batch reading. |
| LingBot adapter | `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py` | Contains the real LingBot-Fast policy/VAE load path, Plücker/camera condition path, flow target, and no-grad forward used by the true smoke. |
| Model discovery | `cam_physgeo/training/model_loading.py` | Resolves LingBot Base/Fast/code roots and identifies Base high-noise/low-noise branch layout versus Fast sharded checkpoints. |
| Warmup smoke | `cam_physgeo/training/lingbot_warmup_smoke.py` | Upgraded this round from placeholder tensor dry-run to true component load and true forward-loss dry-run. |
| DPO | `cam_physgeo/dpo/*`, `docs/stage2_videogpa_dpo_plan.md` | Later-stage preference optimization; not run in this task. |

## Current Data Gate

TDW v5 aggressive 2x 200 is the current human-approved camera-visible warmup candidate.

- Manifest: 200 / 200.
- Integrity audit: 200 / 200 valid.
- Split: train 160, val 20, test 20.
- Dataloader smoke: passed.
- `use_action=false`: passed.
- Dummy `action.npy`: norm 0.0.

## Placeholder Identified

Before this task, `cam_physgeo/training/lingbot_warmup_smoke.py` returned `passed_placeholder_no_model_load`; it only allocated zero tensors and did not load LingBot-Fast, Wan VAE, T5/text path, scheduler, or camera condition into the model forward.

That placeholder cannot satisfy the warmup pre-training gate. This round replaced it with:

- `--mode component_load_smoke`;
- `--mode true_forward_loss_dryrun`;
- `--require_real_model_load true`;
- timestep band reporting.

## PRD Requirements Reinforced

- No real training.
- No DPO training.
- No VideoGPA `03_train`.
- No Stage1 large training.
- No rollout or reward calibration.
- No checkpoint, LoRA, or optimizer state save.
- DPO diagnostic status remains `not_applicable_pre_dpo`.

## Minimal Objective For This Round

Use the existing v5 200 data and the real LingBot-Fast runtime to prove that a no-grad forward-loss can be computed with real model/VAE/text/camera components and logged timestep/sigma bands.
