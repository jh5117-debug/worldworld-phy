# LingBot Camera Trainable Scope Inventory

## Status

- Mode: `list_camera_trainable_scopes`
- Result: passed.
- Training: no.
- Backward: no.
- Optimizer: no.
- GPU: `CUDA_VISIBLE_DEVICES=6,7`; LingBot used physical GPU 6 as `cuda:0`.
- Raw inventory JSON:
  `local_assets/outputs/smoke/lingbot_camera_trainable_scopes/camera_trainable_scope_inventory.json`

The raw run emitted progress/warning output from checkpoint loading. The report
does not repeat the long raw warning text; it is preserved in the command output
and the inventory JSON.

## Model

- Pipeline class: `WanI2VFast`
- Policy model class: `WanModelFast`
- Forward signature:
  `(x, t, context, seq_len, y=None, dit_cond_dict=None, kv_cache=None, crossattn_cache=None, current_start=0, max_attention_size=1000000)`
- Total model params: `23,788,851,264`
- All params were frozen during inventory.
- Physics adapter remained disabled.

## Camera / Action / Control Modules

Key modules found:

- `patch_embedding_wancamctrl`
- `c2ws_hidden_states_layer1`
- `c2ws_hidden_states_layer2`
- `blocks.*.cam_injector_layer1`
- `blocks.*.cam_injector_layer2`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

These modules are used in the camera-conditioned forward path that consumes
`c2ws_plucker_emb`.

## Candidate Counts

- Full `camera_adapter`: `4,255,431,680` params across `326` tensors.
- `action_scale_shift_tiny` candidate pool: `4,195,123,200` params across
  `320` tensors, but the implemented safe selection opens only small biases.
- `plucker_projection_only` candidate pool: `60,308,480` params across `6`
  tensors, but safe selection opens only three biases.
- `head_only`: `337,984` params across `3` tensors.
- Existing LoRA params: none.
- `camera_lora_tiny`: skipped unless LoRA params are already injected.
- `qkv_lora_tiny`: skipped unless LoRA params are already injected.

## Safe Scope Preview

- `action_scale_shift_tiny`: available, `819,200` trainable params.
  Selected late-block bias tensors such as
  `blocks.39.cam_shift_layer.bias`, `blocks.39.cam_scale_layer.bias`,
  `blocks.39.cam_injector_layer2.bias`, and neighboring late blocks.
- `plucker_projection_only`: available, `15,360` trainable params.
  Selected:
  `c2ws_hidden_states_layer2.bias`,
  `c2ws_hidden_states_layer1.bias`,
  `patch_embedding_wancamctrl.bias`.
- `head_only`: available, `337,984` trainable params.
- `tiny_subset`: available, `327,744` trainable params.
- `camera_lora_tiny`: skipped, no existing LoRA params.

## Recommendation Before Sweep

The inventory recommended `action_scale_shift_tiny` as the first meaningful
camera-related scope because it is directly tied to camera scale/shift injection
and is far smaller than full `camera_adapter`.

The full `camera_adapter` remains high risk because it already OOMed near
95-100 GB in the previous backward-only run.
