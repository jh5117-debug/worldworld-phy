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

## Refined blocker and patch

A previous checkpoint-eval log shows the stall inside `WanModelFast.__init__ -> init_weights() -> torch.nn.init.xavier_uniform_` before pretrained shards finish loading. The eval wrapper now also monkey-patches `WanModelFast.init_weights` to a no-op during `from_pretrained`, because the pretrained shards should populate model parameters and the random initialization is unnecessary for this inference-only load path.
