# LingBot Trainable Scope Report

## Status

- Mode: `list_trainable_candidates`
- Result: passed.
- Training: no.
- Backward: no.
- Optimizer: no.
- Model: `WanModelFast` through `WanI2VFast`
- Checkpoint: `local_assets/cache/lingbot_fast_cam_runtime`
- GPU: `CUDA_VISIBLE_DEVICES=6,7`, physical GPU 6 used as `cuda:0`.

## Candidate Scopes

- Existing LoRA params: none found.
- Camera/control adapter candidate params: `4,255,431,680` parameters across
  `326` tensors.
- Tiny subset candidates: available.

Camera/control candidate examples:

- `patch_embedding_wancamctrl.weight`
- `c2ws_hidden_states_layer1.weight`
- `c2ws_hidden_states_layer2.weight`
- `blocks.*.cam_injector_layer*`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

## Selected Strategy

Recommended semantic scope: `camera_adapter`.

Safety concern: opening all camera/control tensors is too large for a
backward-only smoke. The implementation freezes everything first and then opens
only a bounded subset. The first `camera_adapter` attempt used a late-block
selection under `50,000,000` params, but still OOMed during the true backward
run.

Fallback scope used: `tiny_subset`.

Selected tiny subset:

- `head.head.bias`
- `head.head.weight`

Trainable params in fallback: `327,744`.

This is not a training plan. It only proves that the DPO scalar can backprop
through the real LingBot forward path while the reference model remains frozen.
