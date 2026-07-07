# DPO Utility Calibration v14 Status

Updated: `2026-07-07T06:06:00.444732Z`

## Current Decision

`DPO_RECIPE_NOT_FOUND_V14`

## New Progress

- `E01_screen20` ran on physical GPU4 for 20 steps and passed training signal.
- `E06_screen20` ran on physical GPU5 for 20 steps and passed training signal.
- `E06_screen20` checkpoint eval was attempted but blocked at `WanI2VFast` initialization before any videos were generated.

## Best Training-Signal Candidates

- `E06_screen20`: normalized clipped loser alpha=0.05, mean winner improvement post `0.0001410573720932007`, final `0.00028055906295776367`, WCR `0.8179387603935927`.
- `E01_screen20`: raw calibrated winner-detached, mean winner improvement post `0.00014046728610992432`, final `0.0002976655960083008`, WCR `0.9046868415246985`.

## Why This Is Not Solved

The v14 final gate requires training signal plus checkpoint videos plus metrics plus Codex visual audit. E06 could not complete checkpoint video generation because V2V-5 eval stalled at `instantiate WanI2VFast` with no GPU allocation and 0 MP4 outputs. Earlier E02_best7, E04, and E05 generated videos but failed visual gates.

## Scale Permission

- S16/S32/S64: blocked until a scheme passes video/metrics/Codex audit.
- train400: blocked.
- large DPO: blocked.

## Constraints Honored

This update used only physical GPU4/5 for the new E01/E06 screen. No train400, no large DPO, no StageA/StageB/GRPO, no broad-LoRA, no checkpoint deletion, and no videos/weights pushed.
