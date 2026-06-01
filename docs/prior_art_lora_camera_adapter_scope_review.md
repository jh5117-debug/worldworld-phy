# Prior Art: LoRA and Camera-Adapter Trainable Scope

## Scope

This review is for a 1-pair backward-only dry-run. It does not authorize
training, optimizer steps, LoRA saving, checkpoint saving, rollout generation,
reward calibration, or TDW/Physion generation.

## Files Checked

VideoGPA:

- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-I2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX1.5-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/README.md`
- `local_assets/third_party/VideoGPA/official_repo/replicate.py`

LingBot / Wan:

- `local_assets/third_party/lingbot_world/scripts/train_lingbot_dpo_lora.py`
- `/home/nvme03/workspace/lingbot-world/scripts/train_lingbot_dpo_lora.py`
- `local_assets/third_party/lingbot_world/scripts/train_lingbot_sft_lora.py`
- `local_assets/third_party/lingbot_world/scripts/train_lingbot_physics_predictor.py`
- `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`
- `/home/nvme03/workspace/lingbot-world/wan/modules/model_fast.py`
- `local_assets/third_party/lingbot_world/wan/modules/animate/animate_utils.py`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`

## VideoGPA Trainable Handling

VideoGPA uses parameter-efficient LoRA/PEFT rather than full transformer
fine-tuning in the official train scripts. The CogVideo scripts target
attention projections such as `to_q`, `to_k`, `to_v`, and `to_out.0`. The Wan
script uses PEFT LoRA with target modules `q`, `k`, `v`, and `o`.

The reference transformer is separately loaded, put in eval mode, and frozen
with `requires_grad_(False)`. DPO loss compares policy prediction-error
improvement against reference prediction-error improvement. Optimizer setup and
LoRA saving live only inside the official training scripts and are out of scope
for this dry-run.

## LingBot / Wan LoRA References

LingBot has local LoRA code in `scripts/train_lingbot_dpo_lora.py`:

- `LoRALinear`;
- `inject_lora`;
- `set_lora_active`;
- freeze-first parameter handling;
- DPO-specific high/low model toggling.

The existing adapter does not inject LoRA in this round. `camera_lora_tiny` and
`qkv_lora_tiny` are therefore valid only if LoRA parameters already exist in the
loaded model. If no LoRA parameters exist, those scopes must be skipped rather
than synthesized into a fake training path.

## Camera / Plucker / Action Modules

`wan/modules/model_fast.py` defines the camera path used by LingBot-Fast:

- `patch_embedding_wancamctrl`;
- `c2ws_hidden_states_layer1`;
- `c2ws_hidden_states_layer2`;
- per-block `cam_injector_layer1`;
- per-block `cam_injector_layer2`;
- per-block `cam_scale_layer`;
- per-block `cam_shift_layer`.

The forward path transforms `c2ws_plucker_emb`, then injects camera scale/shift
inside blocks. These modules are directly related to camera condition and are
more semantically meaningful than the fallback `head.head.*` subset.

## Small Candidate Scopes

Recommended scopes for this round:

- `action_scale_shift_tiny`: late camera scale/shift/injector parameters,
  bias-first and capped by `max_trainable_params`.
- `plucker_projection_only`: Plucker/camera projection parameters,
  bias-first because full projection weights are large.
- `head_only`: the previous successful output-head plumbing baseline.
- `tiny_subset`: generic fallback only; useful for proving autograd plumbing,
  not a meaningful training plan.
- `camera_lora_tiny`: skipped unless LoRA params already exist.
- `qkv_lora_tiny`: skipped unless LoRA params already exist.

## Why Full Camera Adapter OOMed

The previous `camera_adapter` scope opened camera/control parameters under a
large cap and still OOMed during real backward, peaking around 95-100 GB. The
issue is not only parameter count; opening early camera/control paths retains a
large DiT autograd graph for 8-frame 480x832 latents.

## Scope Tested First

This round prioritizes `action_scale_shift_tiny`, because it is directly
camera-related and can be bounded to very small late scale/shift tensors. It is
safer than full `camera_adapter` and more meaningful than `tiny_subset`.

## Why No Optimizer Step

This gate only tests differentiability and reference isolation. An
`optimizer.step()` would update model parameters and become a training
operation. The current user instruction explicitly forbids parameter updates,
LoRA saves, and checkpoints.

## Why Not Full Camera Adapter

Full camera adapter backward already OOMed. The next useful step is a small
camera-aware scope sweep, not repeating the known high-risk full scope.
