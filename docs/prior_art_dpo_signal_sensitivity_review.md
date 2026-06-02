# Prior Art Review: DPO Learning-Signal Sensitivity Diagnostic

## Current Question

The fixed-noise/fixed-timestep 1-pair LoRA diagnostic passed safety checks, but
the loss stayed essentially at `log(2)`. This round asks whether the weak signal
comes from too small a learning rate, too narrow a camera-control LoRA target, a
very small LoRA forward contribution, or a sign/target issue.

## Files Checked

Local code checked:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/lora_utils.py`
- `cam_physgeo/training/model_loading.py`
- `configs/cam_physgeo/stage1_warmup.yaml`
- `configs/cam_physgeo/stage1_physion_warmup.yaml`
- `configs/cam_physgeo/stage2_anchored_dpo.yaml`
- prior reports under `docs/`

Remote third-party source checked:

- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- VideoGPA LoRA adapter configs under
  `local_assets/third_party/VideoGPA/official_repo/checkpoints/*/adapter_config.json`
- `local_assets/third_party/lingbot_world/generate.py.bak_20260515_195834_pre_prefix_rollout`
- `/home/nvme03/workspace/lingbot-world`

Remote grep was saved under
`local_assets/outputs/smoke/prior_art_dpo_signal_sensitivity_grep.txt` and was
not submitted to git.

## LR / Beta / LoRA Notes

- VideoGPA CogVideoX uses `learning_rate=5e-6`, `beta=1.0`,
  `lora_rank=64`, `lora_alpha=128.0`, and attention targets
  `to_q`, `to_k`, `to_v`, `to_out.0`.
- VideoGPA Wan2.2 TI2V uses `learning_rate=5e-6`, `beta=1.0`,
  `lora_rank=64`, `lora_alpha=128.0`, and attention targets `q`, `k`, `v`,
  `o`.
- The local adapter deliberately uses a much smaller diagnostic setting:
  `AdamW`, lr `1e-5`, rank-2 camera-control LoRA, and beta `0.1`.
- Local guarded smoke configs also use low learning rates around `1e-5`.
- The scalar DPO loss is
  `-log sigmoid(beta * ((E_loser - E_winner)_policy - (E_loser - E_winner)_ref))`.
- With identical policy/reference at initialization, loss near `log(2)` is
  expected.
- Beta scales the observable logit. A small beta can make meaningful but tiny
  energy changes hard to see in the scalar loss.

## Why Fixed-Noise Sensitivity

The previous fixed-noise run removed per-step noise/timestep variation, so loss
and `Delta_policy` became directly comparable across steps. Since the observed
change was still tiny, the next bounded diagnostic is:

- no-step LoRA functional influence probe;
- fixed-noise LR sweep;
- optional fixed-noise scope sweep if LR is stable but still weak;
- optional beta/sign logging if loss direction looks wrong.

The VideoGPA scripts normally resample timesteps and noise per step:

- CogVideoX samples random timesteps and `torch.randn_like(x_win)` noise, then
  applies the same noise/timestep to winner and loser.
- Wan2.2 TI2V samples timesteps, computes flow-matching sigma, applies the same
  noise to winner and loser, and uses target velocity `noise - z_0`.

Therefore fixed-noise is a diagnostic, not the standard training loop.

## LoRA Scope Rationale

Current target modules:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

These are camera/control related and small enough to avoid the full
camera-adapter OOM seen earlier. They may also be weak because they are only the
last block's camera scale/shift path. A broader but still bounded candidate is
the last two or last four blocks' camera shift/scale layers.

## Why Not Save LoRA Or Expand Pairs

This is still a diagnostic:

- no checkpoint save;
- no LoRA save;
- no multi-pair DPO;
- no VideoGPA `03_train.py`;
- no rollout/reward/data generation.

The next pair-count expansion should only happen if the same-pair signal is
measurable and sign-consistent.

## Learnable Signal Criteria

A useful signal would show at least one of:

- scaled LoRA changes policy energy versus no-LoRA;
- higher but stable lr increases `Delta_policy` movement without NaN/Inf/OOM;
- a modestly broader camera LoRA scope increases signal while keeping
  base/reference unchanged;
- DPO sign remains consistent: higher `Delta_policy - Delta_ref` lowers loss.

If scaled LoRA has no measurable energy effect, the target modules likely need
to move earlier/broader in the camera/control path. If LR/scope sweeps remain
flat, do not move to 5-pair/10-pair overfit yet.
