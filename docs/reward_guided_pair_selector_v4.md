
# Reward-Guided Pair Selector v4

Current Status: PASS_REWARD_SELECTOR_IMPLEMENTED

Updated: 2026-06-30 12:09:54

## Goal

Protocol v4 uses Cam-PhysGeo reward plus quality gates and Codex visual review to construct DPO preference pairs. The selector is implemented in `cam_physgeo/dpo/reward_guided_pair_selector.py` and used by `scripts/build_reward_guided_protocol_v4.py`.

## Reward Formula

`R_total = w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur`

Weights are saved in `reports/dpo_pair_hardness_v4/reward_selector_weights.json`.

## Backend Status

- Cam-PhysGeo reward selector: `proxy_reward_guided_v4` for synthetic TypeA+/TypeM generation.
- Clean GT winner reward: `clean_gt`.
- PSNR / SSIM-proxy / sharpness: computed for generated candidates.
- LPIPS: not run for full v4 sweep; marked `BLOCKED_NOT_RUN_FOR_SWEEP` in per-pair tables.
- FVD / VBench: `BLOCKED_BY_ENV`, not fabricated.

## Subreward Alignment

Failure types must align with their intended subreward drop:

- background drift -> `margin_bg` or `margin_cam`
- wrong camera -> `margin_cam`
- object deformation / identity / fragments -> `margin_fg`
- reobserve mismatch -> `margin_reobs`
- physical event failure -> `margin_phys`
- partial freeze -> `margin_freeze`

Alignment output: `reports/dpo_pair_hardness_v4/subreward_alignment.csv`.

## Result

Accepted v4 pairs: 42 total, with 34 TypeA+ and 8 TypeM. TypeB usable remains 0.
