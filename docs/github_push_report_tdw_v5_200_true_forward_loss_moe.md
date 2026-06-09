# GitHub Push Report: TDW v5 200 True Forward-Loss / MoE Gate

Date: 2026-06-09

| Field | Value |
|---|---|
| Branch | `physion-tdw-v5-200-true-forward-loss-moe` |
| Remote | `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git` |
| Final commit | branch HEAD after push; see `git log -1 --oneline` |
| Commit message | `Add MoE-aware true LingBot forward-loss smoke for TDW v5 200` |
| Push status | pushed to origin |

## Scope Pushed

- `cam_physgeo/training/lingbot_warmup_smoke.py`
- `docs/*.md`

## Excluded

- `local_assets/`
- generated HDF5 / MP4 / NPY / NPZ
- logs
- weights / checkpoints / LoRA / safetensors
- latents
- third-party raw repo payloads

## Verification

- Local syntax check passed for `cam_physgeo/training/lingbot_warmup_smoke.py`.
- No staged file matched `local_assets`, generated assets, weights, checkpoints, LoRA, or latents.
- True LingBot-Fast component load and no-grad forward-loss smoke passed on H20 GPU7.
