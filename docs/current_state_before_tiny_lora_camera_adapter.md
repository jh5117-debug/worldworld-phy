# Current State Before Tiny LoRA Camera Adapter

## Summary

- Previous branch: `physion-dpo-trainable-scope-sweep`
- Previous commit: `09f665a0e8242793807798b51eed580f338a050d`
- Remote execution directory:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_energy_forward_work`
- `local_assets` remains a symlink to the shared asset tree.
- No local assets, videos, latents, weights, HDF5, NPY/NPZ/PT/PTH, or
  safetensors were moved or deleted.

## Previous Scope Sweep

`camera_adapter`-style existing parameter scopes failed because the
camera/control path retains a large DiT autograd graph at the current
8-frame 480x832 latent size.

- `plucker_projection_only`: OOM, peak about `100.44 GB`.
- `action_scale_shift_tiny`: OOM, peak about `100.48 GB`.

The passing scopes were:

- `tiny_subset`: passed, `327,744` trainable params.
- `head_only`: passed, `337,984` trainable params.

Both are useful only for gradient plumbing. They are not camera-aware and are
not recommended for optimizer-step dry-run.

## LoRA State

- `camera_lora_tiny` was skipped because the loaded LingBot-Fast model had no
  existing LoRA/PEFT parameters.
- Existing third-party LoRA examples exist, but no LoRA was injected into this
  adapter before this round.

## Current Permission State

- Optimizer step: not allowed.
- Real training: not allowed.
- LoRA/checkpoint save: not allowed.
- This round is limited to a runtime tiny LoRA/camera adapter injection and
  1-pair backward-only dry-run.
