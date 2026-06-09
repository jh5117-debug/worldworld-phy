# GitHub Push Report: TDW v5 200 Warmup Gate

Date: 2026-06-09

## Branch

- Branch: `physion-tdw-v5-200-warmup-gate`
- Commit: branch head after final push
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit

Message:

`Add TDW v5 200 LingBot warmup gate audits`

## Scope Pushed

Code:

- `cam_physgeo/data/tdw_generation_v2/build_lingbot_dataset_manifest.py`
- `cam_physgeo/data/tdw_generation_v2/audit_lingbot_dataset.py`
- `cam_physgeo/data/tdw_generation_v2/split_lingbot_dataset.py`
- `cam_physgeo/training/lingbot_dataset_smoke.py`
- `cam_physgeo/training/lingbot_warmup_smoke.py`

Docs:

- TDW v5 manifest, audit, split, dataloader, forward-smoke, approval, and final reports.
- PRD / Stage2 / generation plan / generation spec / experiment registry updates.

## Excluded

The push excludes `local_assets/`, generated HDF5, MP4, NPY/NPZ, logs, weights, checkpoints, LoRA files, latents, and raw third-party repositories.

## Safety

No training, DPO, VideoGPA `03_train`, Stage1, rollout, reward calibration, TDW generation, checkpoint save, or LoRA save was run in this gate.
