# Prior Art Review: 5-Pair Tiny DPO Overfit Smoke

## Files And Sources Checked

Local docs/code:

- `docs/prior_art_dpo_overfit_miniloop_review.md`
- `docs/prior_art_fixed_noise_dpo_diagnostic_review.md`
- `docs/prior_art_dpo_signal_sensitivity_review.md`
- `docs/final_report_fixed_noise_dpo_diagnostic.md`
- `docs/signal_sensitivity_summary.md`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/lora_utils.py`

Local VideoGPA official repo path:

- `local_assets/third_party/VideoGPA/official_repo`

This path was not present in the local scratch worktree. Prior remote reviews
already inspected the VideoGPA official train scripts on the GPU worktree:

- `train/CogVideoX-5B/03_train.py`
- `train/Wan2.2-TI2V-5B/03_train.py`
- `train/dataset.py`

Public references checked:

- VideoDPO official GitHub:
  `https://github.com/CIntellifusion/VideoDPO`
- VideoGPA official GitHub:
  `https://github.com/Hongyang-Du/VideoGPA`

## VideoGPA Loop Pattern

Prior remote inspection found that VideoGPA organizes the workflow as:

1. preference pair export;
2. latent encode;
3. LoRA DPO training in `03_train.py`.

The official trainers use dataloaders, LoRA trainable parameters, AdamW, random
noise/timestep sampling per step, and same noise/timestep for winner and loser
within a pair. They also include normal training features such as checkpointing
and final adapter save paths, which remain disabled in this project smoke.

## Noise / Timestep Policy

For real training-style loops, VideoGPA resamples noise/timestep per step while
sharing the sampled noise/timestep across winner and loser in the same pair.

For diagnostics, fixed noise/timestep is useful because it makes
`Delta_policy` and loss movement interpretable across steps. The previous
fixed-noise run used this diagnostic setting and showed stability, but not a
meaningful monotonic overfit signal.

## Gradient Accumulation

The proposed 5-pair smoke should use:

- `batch_size=1`;
- `gradient_accumulation_steps=1`;
- at most `10` steps;
- pair cycling over an at-most-5-pair set.

This validates dataloader/pair cycling and LoRA-only updates. It is not a
training run.

## VideoDPO Preference Notes

VideoDPO uses preference pairs derived from an automatic scoring pipeline and
reports that score-based pair reweighting matters for preference alignment.
For this project, reward margin can be preserved as metadata and later used as
a weight, but the current 5-pair smoke should not add new weighting complexity
until the one-pair learning signal is stronger.

## How 5-Pair Should Be Organized If Allowed

If the signal gate passed, the 5-pair smoke should:

- use existing `gt_vs_fast` pairs first;
- fill with existing `gt_vs_corrupt` pairs only if needed;
- generate no new rollout;
- run LingBot/Wan VAE encode, not VideoGPA native VAE;
- preserve prompt, condition image, poses, intrinsics, dummy action, and
  `use_action=false`;
- use LoRA target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`, unless a later
  scope diagnostic selects a better target;
- use same noise/timestep within winner/loser for each step;
- resample noise/timestep per step for normal multi-pair smoke;
- keep LoRA/checkpoint saving disabled.

## Current Gate Decision

Do not run 5-pair tiny overfit yet.

Reasons:

1. LoRA functional influence passed.
2. Target modules affect the real forward path.
3. The default rank-2 energy movement is extremely small.
4. The full LR sweep did not complete.
5. The only higher-LR evidence is one `lr=1e-4` step with a tiny logit.
6. Scope sweep did not run.
7. The recommended scope is still provisional.

## Why This Is Still Not Training

Even if 5-pair were allowed, it would remain a smoke test:

- no VideoGPA `03_train.py`;
- no checkpoint save;
- no LoRA save;
- no multi-pair full run;
- no TDW generation;
- no reward calibration;
- no rollout generation.

## Next Gate Before 10-Pair

Before 10-pair or any larger smoke:

1. Complete a short optimized LR sensitivity run.
2. Test current and last-2-block camera LoRA scopes.
3. Confirm finite gradients and nonzero energy/logit movement.
4. Confirm base/reference immutability.
5. Only then ask the user before expanding pair count.
