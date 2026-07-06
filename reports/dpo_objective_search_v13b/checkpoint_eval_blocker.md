# v13b Checkpoint Eval Blocker

Updated: 2026-07-06T15:32:53

## Status

- Best training-signal scheme: `S01_winner_detached_pref_low`.
- Training signal is positive, but this is not enough to accept a DPO recipe.
- Checkpoint V2V-5 rollout is required for step0/best/final before metrics and Codex audit.

## Blocker

The checkpoint eval path stalled at WanI2VFast / `WanModelFast.from_pretrained` before producing any video. Existing older overnight rollout jobs on GPU4/5 show the same symptom: selected manifests exist, but no MP4 outputs.

## Non-destructive fix applied

`cam_physgeo/eval/run_fast_adapter_inference.py` now monkey-patches `WanModelFast.from_pretrained` in the eval wrapper to force:

- `local_files_only=True`
- `use_safetensors=True`
- `low_cpu_mem_usage=True`

This avoids editing external LingBot source and should be tested once GPU4 or GPU5 is free.

## Gate

Decision remains `DPO_RECIPE_TRAINING_SIGNAL_ONLY`. No `DPO_RECIPE_FOUND_200STEP` until checkpoint videos, metrics, and Codex visual audit pass.
