# Camera Condition Runtime Debug Report

## Runtime Debug Output

Debug condition files were written under:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke/physion_movingcam_07abddf5748b/*/physion_movingcam_07abddf5748b/condition_debug.json
```

For all attempted variants:

- `poses_input_shape`: `[81, 4, 4]`
- raw `intrinsics_shape`: `[81, 4, 4]`
- converted `intrinsics_shape`: `[81, 4]`
- `action_shape`: `[81, 4]`
- `use_action`: `false`
- dummy action norm: `0.0`
- `camera_condition_passed_to_pipeline`: `true`

The runtime signature reported:

```text
input_prompt, img, action_path, physics_teacher_tokens, physics_gate_scalar,
physics_use_raw_cross_attn, physics_debug_direct_inject, physics_debug_manual_attn,
physics_debug_capture, stop_after_first_step, chunk_size, max_area, frame_num,
timesteps_index, shift, seed, offload_model, max_sequence_length, max_attention_size
```

## Embedding Hook Status

The current debug confirms that `action_path` reaches `WanI2VFast.generate` and that the condition directory contains nonzero poses plus converted intrinsics. It does not yet hook the internal `c2ws_plucker_emb` tensor after `get_plucker_embeddings`, so:

- `plucker_or_camera_embedding_shape`: `null`
- `plucker_or_camera_embedding_norm`: `null`

## Variant Tensor Differences

The attempted variants wrote distinct pose tensors:

- `repeat_correct_A`, `repeat_correct_B`, and `correct` have the original pose norm about `32.7261`.
- `frozen` has a different repeated-first-frame pose norm about `32.9503`.
- `reversed` has the same norm as the original but reversed time order.
- `exaggerated_yaw` has the same global norm to numerical precision but modified rotations.

This proves the ablation inputs differ and are passed to the pipeline. It does not prove the generated video responds to those differences because most variants failed before saving video.
