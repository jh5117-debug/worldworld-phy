# Quality-Bounded Hard Negative Design Report

## Why loser cannot be too bad

Current Base/StageA/StageB rollout quality is often too poor to use naive low-score generated videos as DPO losers. If the loser is black, corrupt, severely blurry, flickering, missing objects, or hallucinating extra objects, the DPO signal teaches generic quality cleanup rather than camera-conditioned physical reasoning.

## Config

Config added: `configs/cam_physgeo/quality_bounded_hard_negative.yaml`.

Quality floor:

- `R_quality >= 0.55`
- reward confidence >= 0.50
- reject black/corrupt videos
- reject severe blur/flicker
- reject object disappearance
- reject extra object hallucination when detectable

Hard negative policy:

- Loser must be acceptable quality.
- Loser should be worse in one or more of `R_cam`, `R_bg`, `R_fg`, `R_phys`, `R_reobs`.
- Margin should be neither too small nor too large: default 0.03 to 0.25.

## DPO status

This is a pair mining policy only. DPO training was not run.
