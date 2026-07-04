# DPO Training Sanity v12 Report

## Data

Used canonical repaired ready500 manifest and repaired train/val/test splits. Old ready500 was not used.

## LoRA Scope Sanity

Best scope: `L0_camera_r4`.

- `L0_camera_r4`: PASS, mean winner improvement `3.560781478881836e-05`, final `0.00015497207641601562`.
- `L1_camera_r8`: FAIL, mean `-4.541873931884766e-06`, final `-0.00016415119171142578`.
- `L2_camera_temporal_r4`: FAIL, mean `2.429485321044922e-05`, final `-1.1920928955078125e-07`.
- `L3_camera_cross_r4`: FAIL, mean `-1.5294551849365236e-05`, final `-0.00019311904907226562`.

Conclusion: camera-only rank4 is the only scope that passed the explicit winner-anchor gate. Camera-r8 and broader attention scopes were not safer in this sanity check.

## Tiny DPO Run

Run: `strict_sdpo` guarded anchor proxy on S1 32 pairs with `L0_camera_r4`.

- Cache: `32/32 PASS`.
- Requested: 20 steps.
- Completed before stop: `11` rows.
- Mean winner improvement post: `-7.748603820800781e-07`.
- Final winner improvement post: `-0.00018405914306640625`.
- Mean loser degradation post: `-2.373348582874645e-06`.
- Final loser degradation post: `1.1920928955078125e-05`.
- Mean winner contribution ratio: `0.43831473876668603`.
- Final winner contribution ratio: `0.0`.
- Mean DPO loss: `0.6931492632085626`.

The run was manually stopped after step10 because winner improvement turned negative and DPO loss stayed at the no-signal regime around 0.693. This is not a successful DPO result.

## Checkpoint Evaluation

Local LoRA checkpoints were saved for step0, step5, and step10 under `local_assets/dpo_training_sanity_v12/guarded_sdpo_anchor_s1/checkpoints/`. Because the energy signal already failed, checkpoint rollout/video audit was not run and no visual PASS is claimed.

## Decision

`DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`.

Large DPO remains blocked. The next action is to revise the objective before further training, likely delaying loser terms longer, reducing or removing the preference sigmoid branch until winner improvement is robust, and adding an automatic stop rule inside the runner.
## Verification

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Pytest: unavailable in `/usr/bin/python3` (`No module named pytest`); no pytest PASS is claimed.
