# PhysEditWorld Post-Mount Continuation Summary

Decision: `POST_MOUNT_BLOCKED_AT_ROOT_INPUT`

## Steps

- `root_input`: `BLOCKED`
  - command: `PHYS_EDITWORLD_ROOTS`
  - decision: `POST_MOUNT_BLOCKED_NO_ROOTS`
  - error: set PHYS_EDITWORLD_ROOTS=/path/to/selected_50h_root

## Safety

This continuation runs only Phase 1/2 CPU/IO preparation and safe gate collectors. It does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, or deletion.
Smoke conversion writes a non-canonical smoke manifest. Canonical LingBot train/val/test manifests are written only when `--run_full_conversion` is explicitly set.
