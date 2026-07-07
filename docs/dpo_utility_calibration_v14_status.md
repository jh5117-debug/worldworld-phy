# DPO Utility Calibration v14 Status

Updated: `2026-07-07T05:04:09.871964Z`

## Current Decision

`DPO_RECIPE_NOT_FOUND_V14`

## What Ran

- E02_smoke10: calibrated winner-detached log objective, training signal failed because final winner improvement flipped negative.
- E03_smoke10: lower-LR calibrated objective, stopped early for winner worse.
- E02_best7: training signal passed, but checkpoint video audit failed.
- E04_screen5: no-lose-gap normalized winner-only backbone passed training signal, but checkpoint video audit failed.
- E05_screen5: normalized clipped loser objective passed training signal, but checkpoint video audit failed.

## Latest E05 Result

- Objective: `normalized_clipped_loser`
- Steps: `5`
- Mean winner improvement post: `0.00012555122375488282`
- Final winner improvement post: `0.00012230873107910156`
- Mean winner contribution ratio: `0.8245008192953873`
- Checkpoint videos: `8` true V2V-5 videos generated for step000/step005
- Metrics: `8/8` PSNR/SSIM/LPIPS rows OK
- Visual audit: `2/4` samples worse at step005
- Decision: `VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`

## Interpretation

E05 is the best DPO-like training-signal candidate so far, but it is not a solved recipe because the final checkpoint still worsens real videos. Per the project gate, training gaps alone do not permit scale.

## Scale Permission

- S32/S64: blocked
- train400: blocked
- large DPO: blocked

## Constraints Honored

No large DPO, no train400, no StageA/StageB/GRPO, no broad-LoRA, no checkpoint deletion, and no videos/weights pushed.
