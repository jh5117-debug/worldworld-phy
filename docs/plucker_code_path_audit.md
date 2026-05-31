# Plucker Code Path Audit

The actual LingBot-Fast runtime lives under:

`local_assets/third_party/lingbot_world/wan/image2video_fast.py`

The direct import probe had one malformed heredoc attempt, but static path audit succeeded against the local LingBot checkout.

## Key Paths

- Plucker utility: `local_assets/third_party/lingbot_world/wan/utils/cam_utils.py`, `get_plucker_embeddings(...)`.
- Fast generator camera load path: `local_assets/third_party/lingbot_world/wan/image2video_fast.py`.
- `action_path` is accepted by `WanI2VFast.generate(...)`.
- `poses.npy` is loaded when `action_path is not None`.
- `intrinsics.npy` is loaded in the camera preparation block.
- `get_Ks_transformed(...)`, pose interpolation, relative pose conversion, and `get_plucker_embeddings(...)` build `c2ws_plucker_emb`.
- With `control_type="act"`, LingBot concatenates Plucker camera features with `action.npy`; our action tensor is dummy zero.
- Fast DiT consumes `dit_cond_dict["c2ws_plucker_emb"]` in `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`.

## Important Lines From Audit

- `image2video_fast.py:275-283`: `action_path` branch loads `poses.npy` and, for `control_type == "act"`, `action.npy`.
- `image2video_fast.py:346-349`: camera preparation starts and loads `intrinsics.npy`.
- `image2video_fast.py:380-399`: `get_plucker_embeddings(...)` builds `c2ws_plucker_emb`; dummy action is concatenated only after Plucker features.
- `image2video_fast.py:450-459`: `c2ws_plucker_emb` is split by chunk and placed into `dit_cond_dict`.
- `modules/model_fast.py:329-333` and `644-662`: Fast DiT consumes the camera control tensor.

## Answer

Camera condition is not merely read from disk; it reaches the LingBot-Fast Plucker/control path. `use_action=false` does not remove the `action_path` camera branch in this runtime. Dummy action is present for compatibility and has zero norm, so it does not introduce real action conditioning.
