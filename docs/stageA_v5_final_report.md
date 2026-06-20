# StageA v5 Broad-LoRA Final Report

Date: 2026-06-20

## Summary

This pass completed code audit and broad-LoRA implementation work, but blocked formal generated_v5 StageA training because no generated_v5 sample currently passes validation.

## Code Changes

- Added explicit StageA v5 broad-LoRA target groups:
  - camera_conditioning
  - self_attention
  - cross_attention
  - ffn
- Added required target group checks.
- Added LoRA target metadata reporting.
- Added real optimizer-step controls:
  - `max_train_optimizer_steps`
  - `min_train_optimizer_steps`
  - `save_every_optimizer_steps`
  - `scheduler_eta_min`
- Added adapter-only `adapter_state.pt` and `adapter_metadata.json` save beside eval-compatible branch checkpoints.
- Added Stage1 dataset preparation from LingBot JSONL manifests.
- Added generated_v5 snapshot tooling.
- Added StageA v5 launch script.

## Validation

Local:

- `compileall`: passed.
- `pytest -q`: passed, 6/6.

Remote:

- `compileall`: passed.
- `pytest`: unavailable in installed H20 Python environments.
- direct broad-LoRA smoke: passed.
- launcher dry-run: passed.

## Data State

Existing 1000 combined_prompt_v2 converted dataset:

- Stage1 prep passed.
- train / val / test = 800 / 100 / 100.
- Missing rows = 0.

generated_v5 scale-up:

- HDF5 count at latest read: 1987.
- TDW tmux sessions alive.
- validated-only snapshot eligible count: 0.
- Chunk reports currently show `Validation ok count: 0` and `blocked`.
- No generated_v5 LingBot conversion outputs are present.

## Safety

- No DPO training.
- No reward scoring.
- No pair construction.
- No rollout candidate generation.
- No StageB.
- No GPU0 training.
- No TDW tmux modification.
- No local_assets or generated data committed.

## Next Required Action

Fix generated_v5 validation/conversion first. Once validated converted samples exist, run GPU7 preflight and then formal StageA broad-LoRA training on non-GPU0 devices.
