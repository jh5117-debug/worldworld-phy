# Stage1 Physion Warm-Up Plan

Stage1 is a short support warm-up, not the final method.

- Use Physion cam-only converted samples.
- Keep action disabled; dummy `action.npy` is compatibility only.
- Use LingBot-Fast when the fast runtime can load the shard layout; otherwise use LingBot-Base branch layout for warm-up integration.
- Use LoRA/adapter only.
- Keep low LR and short run.
- Add TRD auxiliary from the legacy physical consistency code.
- Use reward calibration for early stopping.

The real training path remains guarded behind `--run`.
