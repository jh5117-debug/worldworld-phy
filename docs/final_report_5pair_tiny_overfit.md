# Final Report: 5-Pair Tiny DPO Overfit Gate

## Git / Remote

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Worktree: `/tmp/local_assets_work`
- Branch: `physion-dpo-5pair-tiny-overfit`
- Base commit: `c10853196a3597f6a932d45fd7ac71c22a3abd8e`
- `local_assets`: local/untracked asset root, not submitted.
- Assets moved/deleted: no.
- Submitted assets/videos/latents/weights/HDF5/NPY/PT/safetensors: no.

## Signal-Sensitivity Summary

5-pair tiny overfit was not allowed by the gate.

- LoRA functional influence: passed.
- Target modules affect forward:
  - `blocks.39.cam_shift_layer`;
  - `blocks.39.cam_scale_layer`.
- Default LoRA energy movement: about `5.960e-08`, very weak.
- Scaled LoRA changes energy, so the path is not dead.
- Full LR sweep: runtime-blocked / terminated.
- Fallback `lr=1e-4`, 1 step: passed safely, but preference logit remained
  about `2.831e-08`.
- Scope sweep: skipped.
- Recommended LR: provisional only; `1e-4` is safe for one step but not proven
  for a multi-step 5-pair smoke.
- Recommended scope: provisional current scope; next diagnostic should try
  `last2_blocks_camera` only after optimizing runtime.

## Pairset

Skipped.

No pairset was built because the signal gate failed before Phase A. Existing
pairs were not modified, copied, or regenerated. No new rollout was generated.

## Latent Encode

Skipped.

No 5-pair LingBot/Wan VAE latent encode was run because pairset construction
was not allowed by the signal gate. No latents were written.

## 5-Pair Mini-Loop

Skipped.

Reason: the task gate requires a stable LR, no NaN/Inf/OOM, nonzero signal, and
a recommended scope. The current diagnostics show connected LoRA modules but a
weak default signal, an incomplete LR sweep, and no scope sweep.

## Interpretation

The DPO plumbing is not the blocker anymore. The blocker is learning-signal
quality for the current tiny camera-control LoRA scope. Running 5-pair now
would mostly validate pair cycling and dataloader mechanics, while leaving the
core question unanswered: whether the camera-control LoRA receives a useful DPO
energy signal.

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: partial.
  - VideoGPA pair/metadata dry-run: passed.
  - LingBot latent encode: passed for earlier smoke.
  - Condition encode: passed.
  - Batch shape: passed.
  - Policy/reference energy: passed.
  - Scalar loss: passed.
  - Backward-only and LoRA optimizer-step: passed.
  - 1-pair fixed-noise diagnostic: passed for stability but weak signal.
  - Signal sensitivity: weak / incomplete.
  - 5-pair tiny overfit: skipped.
- Gate F: no. Real DPO training remains disallowed.

## Real Training Permission

Real DPO training is not allowed.

No VideoGPA `03_train.py`, no saved LoRA, no checkpoint, no multi-pair formal
training, no rollout generation, no reward calibration, and no TDW generation
were run.

## Next Minimal Action

Do not move to 5-pair or 10-pair yet. Next:

1. Optimize the signal-sensitivity runner to reuse loaded policy/reference
   models.
2. Run a short fixed-noise LR sweep.
3. If the current target remains weak, run a bounded last-2-block camera LoRA
   scope test.
4. Only after a stronger signal is observed should the user be asked whether to
   run 5-pair or 10-pair tiny overfit.

If the user wants data work instead, the only allowed data action is a
1-sample TDW generation dry-run. Full TDW generation remains gated.
