# Current State Before Stage A Balanced Warmup

Date: 2026-06-09

## Previous Stage A Result

Previous branch: `physion-tdw-v5-200-stageA-warmup-pilot`

Previous commit: `e69740f7e46680236d51a64209e10b6374ab5bc3`

The previous Stage A high-noise pilot passed as a minimal stability gate:

- steps completed: 20;
- train loss finite: 0.030702 to 0.062314;
- val loss finite: 0.033537 and 0.034270;
- timestep: diagnostic high-noise 799;
- sigma: 0.799;
- LoRA trainable params: 40,960;
- LoRA targets: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- LoRA tensors changed: 4;
- sampled frozen base tensors changed: 0;
- no NaN/Inf or OOM;
- no checkpoint, LoRA, or optimizer state saved.

## Why It Was Only A Minimal Pass

The previous training loop read the train manifest in order:

`row = train_rows[(step - 1) % len(train_rows)]`

The first 20 rows in the current split order happened to be all `collision + orbit_right_64`. That proved the real model-load, forward, backward, optimizer, and LoRA update path, but it did not prove balanced warmup across templates or camera variants.

## Why Not Directly Stage B

Stage B would move toward mixed / low-noise detail refinement. That should wait until Stage A is shown stable on a representative sample mix. A collision-only Stage A pass is not enough evidence for broader timestep training.

## This Round

Approved scope:

- implement and audit a balanced sampler;
- run `sampler_dryrun`;
- run balanced Stage A high-noise pilot, max 60 steps;
- save exactly one tiny adapter-only LoRA checkpoint;
- no full model checkpoint;
- no optimizer state;
- no rollout;
- no reward calibration;
- no DPO;
- no VideoGPA `03_train`;
- no new TDW data.
