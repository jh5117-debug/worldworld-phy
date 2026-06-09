# GPU Usage Approval Request: TDW v5 200 Warmup Pilot

Date: 2026-06-09

## Status

Not approved to run yet.

The TDW v5 200 dataset manifest, audit, split, and dataloader smoke passed. The only model-side result so far is a placeholder no-model-load forward dry-run. A real LingBot-Fast model-load forward-loss smoke must pass before a warmup pilot should start.

## Proposed Task

LingBot-Fast camera-conditioned warmup pilot on the human-approved TDW v5 aggressive 2x 200 dataset.

## Dataset

- Train: 160
- Val: 20
- Test: 20
- Source: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- Manifest root: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/`

## Proposed Resources

- GPU: GPU7 preferred, or GPU6/7 if both are free.
- Batch size: 1
- Max steps: 100 to 200
- Trainable params: adapter / LoRA-only if approved; no full-model update.
- Checkpoint: disabled by default. If a checkpoint is needed, request one explicit small checkpoint approval.

## Required Precondition

Run and pass a real LingBot-Fast model-load forward-loss smoke:

- no backward;
- no optimizer;
- no checkpoint;
- local files only;
- 1 to 2 batches;
- verify LingBot-Fast / VAE / text condition / camera condition path.

## Risk

- OOM during model load;
- weak camera response even after TDW warmup;
- overfitting because dataset is only 200 samples;
- accidental checkpoint creation if training script defaults are not locked down.

## Approval Needed

User approval is required before any optimizer step, backward pass, checkpoint save, LoRA save, or warmup training run.
