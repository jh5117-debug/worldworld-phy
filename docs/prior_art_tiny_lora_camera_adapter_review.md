# Prior Art: Tiny LoRA Camera-Control Adapter

## Scope

This review gates a 1-pair backward-only dry-run. It does not allow training,
optimizer steps, LoRA saving, checkpoint saving, rollout generation, reward
calibration, or TDW/Physion generation.

## Files Checked

VideoGPA local official repo:

- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX-I2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/CogVideoX1.5-5B/03_train.py`

LingBot / Wan local repos:

- `local_assets/third_party/lingbot_world/scripts/train_lingbot_dpo_lora.py`
- `/home/nvme03/workspace/lingbot-world/scripts/train_lingbot_dpo_lora.py`
- `local_assets/third_party/lingbot_world/scripts/train_lingbot_sft_lora.py`
- `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`
- `local_assets/third_party/lingbot_world/wan/modules/animate/animate_utils.py`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`

External web references were not required for implementation because the local
third-party repos already include VideoGPA Wan LoRA training code and LingBot
LoRA examples. No third-party source files were modified.

## VideoGPA LoRA Handling

VideoGPA uses parameter-efficient LoRA/PEFT in official training scripts. The
Wan path targets attention projections such as `q`, `k`, `v`, and `o`; CogVideo
paths target projections such as `to_q`, `to_k`, `to_v`, and `to_out.0`.
Reference models are loaded separately, frozen with `requires_grad_(False)`,
and evaluated under `no_grad`.

This round does not reuse VideoGPA trainer code because the objective is not a
training loop. It only borrows the principle: freeze the base policy and expose
a tiny trainable low-rank delta.

## LingBot / Wan LoRA References

LingBot has local LoRA examples with a `LoRALinear` style wrapper and
freeze-first behavior. The loaded LingBot-Fast checkpoint, however, has no
pre-existing LoRA parameters, so the previous `camera_lora_tiny` scope skipped.

The safest implementation is a runtime wrapper around selected `nn.Linear`
modules in the policy model only. It avoids modifying LingBot source or weight
files and avoids saving adapter weights.

## Camera-Control Modules

The LingBot-Fast camera path in `wan/modules/model_fast.py` includes:

- `patch_embedding_wancamctrl`
- `c2ws_hidden_states_layer1`
- `c2ws_hidden_states_layer2`
- `blocks.*.cam_injector_layer1`
- `blocks.*.cam_injector_layer2`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

These modules transform the Plucker/control tensor and inject camera
scale/shift into DiT blocks. They are more camera-relevant than the successful
`tiny_subset` and `head_only` plumbing scopes.

## Why Full Camera Adapter OOMed

The full camera adapter exposes billions of parameters and, more importantly,
retains a large camera-conditioned DiT autograd graph at 8 frames and 480x832.
Previous backward-only attempts OOMed near 100 GB even when the selected
existing tensors were small. Parameter count alone is not sufficient; activation
memory is also the limiting factor.

## LoRA Memory Tradeoff

LoRA reduces trainable parameter gradient memory because the frozen base weights
do not receive gradients. It does not remove activation memory for the wrapped
forward path. Therefore the first LoRA target must be late, tiny, and directly
camera-related.

## Recommended Target

First target:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

Recommended rank/alpha:

- rank: `2`
- alpha: `4`

These targets are late camera-control affine layers. Rank-2 LoRA adds only a
small number of trainable parameters while still touching the camera
scale/shift path. If this OOMs, fallback is rank 1 on
`blocks.39.cam_shift_layer` only.

## Why No Optimizer Step

An optimizer step would update parameters and become training. This gate only
tests whether finite gradients can be produced on a meaningful
camera/control-aware adapter while the reference remains frozen.

## Why Not Full Camera Adapter

Full camera adapter backward is already known to OOM and is too broad for a
first optimizer candidate. A runtime tiny LoRA wrapper is the smallest sensible
next gate.

## License / Third-Party Risk

The implementation lives in `cam_physgeo/dpo/lora_utils.py` and performs
runtime injection only. It does not patch VideoGPA or LingBot third-party code
and does not modify or save model weights.
