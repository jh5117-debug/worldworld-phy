# Camera Condition Path Audit

## Static Path

- Sample `poses.npy`: `(81, 4, 4)`.
- Sample raw `intrinsics.npy`: `(81, 4, 4)` Physion/TDW projection matrices.
- Runtime LingBot intrinsics: `(81, 4)` `[fx, fy, cx, cy]`, written only under each inference output's `lingbot_condition/`.
- `run_inference.py` reads `image.jpg`, `prompt.txt`, `poses.npy`, `intrinsics.npy`, and dummy `action.npy`.
- `run_inference.py` writes:
  - `lingbot_condition/poses.npy`
  - `lingbot_condition/intrinsics.npy`
  - `lingbot_condition/action.npy`
- `WanI2VFast.generate(...)` is called with `action_path=<lingbot_condition>`.

## LingBot-Fast Code Path

Remote audit of `local_assets/third_party/lingbot_world/wan/image2video_fast.py` shows:

- `generate(..., action_path=None, ...)` accepts `action_path`.
- When `action_path is not None`, it reads `poses.npy` and `intrinsics.npy`.
- It transforms intrinsics with `get_Ks_transformed`.
- It interpolates camera poses, computes relative poses, and calls `get_plucker_embeddings(...)`.
- It passes `c2ws_plucker_emb` through `dit_cond_dict`.
- `wan/modules/model_fast.py` consumes `dit_cond_dict["c2ws_plucker_emb"]` in the camera injection block.

## Action / Camera Interaction

- The sample metadata keeps `use_action=false`.
- Runtime dummy `action.npy` has norm `0.0`.
- In `image2video_fast.py`, `action.npy` is loaded only when `self.control_type == "act"`.
- The current Fast camera path uses camera/Plucker conditioning through `action_path`, not real action-following.
- `use_action=false` does not by itself disable the camera path; camera is active when `action_path` is provided and `poses.npy` / `intrinsics.npy` exist.

## Risk

The pipeline is not merely image+prompt at the call-signature level: `action_path` is passed and LingBot-Fast has code to convert that directory into `c2ws_plucker_emb`. However, the current runtime debug still does not hook the internal embedding tensor norm after `get_plucker_embeddings`, and strong ablation did not produce enough successful variants to prove a visible generation effect. Gate C remains not proven.
