# v14 Self Review

Updated: `2026-07-07T23:12:51Z`

## What Improved

- The beta/no-signal root cause is now understood: old beta=0.1 was far too small for observed utility scale.
- CUDA runtime repaired the one-pair real-energy path and calibration4 produced 4/4 real LingBot energy rows.
- DINOv2 and V-JEPA2 local latent monitors now produce real scores without downloads.
- V-JEPA2 distinguishes every available WIN/LOSE pair in broad monitor coverage: 74/74 positive token-relation margins.

## What Still Fails

- v14 did not find a DPO recipe that passes both scalar and true-video gates.
- Scalar-improving schemes still degrade V2V-5 checkpoint videos.
- E07/E09/E10 are not valid recipes despite good winner/gap metrics.
- S_pass and rollout-only latent scoring are blocked by missing old loser video assets.
- all500 real LingBot energy is still blocked by runtime/cache cost and asset completeness.

## Decision

`DPO_RECIPE_NOT_FOUND_V14` and `NO_SCALE` remain correct. Do not run S16/S32/train400/large DPO from v14.

## Next Safe Action

Start v15 as a monitor/regularizer experiment: use V-JEPA2/DINO latent margins to gate or penalize artifact amplification before another tiny calibrated DPO search.

## Artifact Hygiene

Only source/tests/docs and small CSV/JSON/MD summaries were pushed. No videos, images, local_assets, checkpoints, weights, or large logs were pushed.


## Calibration8 real-energy extension

A bounded follow-up run extended real LingBot energy coverage from 4 to 8 asset-complete v11 synthetic controlled pairs on physical GPU5. This strengthens the gap-scale evidence and shows one negative Delta_ref case, but it still does not satisfy all500/S_pass/rollout real-energy coverage and does not change the `DPO_RECIPE_NOT_FOUND_V14` decision.


## Calibration12 real-energy extension

A bounded resume run extended real LingBot energy coverage from 8 to 12 asset-complete v11 synthetic controlled pairs on physical GPU5. The expanded sample still has exactly zero policy-reference utility at initialization, while Delta_ref spans a useful range including one negative row. This strengthens calibration evidence but still does not satisfy all500/S_pass/rollout real-energy coverage and does not change the `DPO_RECIPE_NOT_FOUND_V14` decision.
