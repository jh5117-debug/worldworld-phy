# Final Report: Camera Condition / Reward Debug

## 1. Summary

- Status: `partial_success`.
- Scope respected: no training, no DPO, no VideoGPA encode, no Stage1 warm-up, no data/weight deletion.
- Worktree used on H20: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`.
- Local branch prepared for push: `physion-camera-reward-debug`.
- Remote run dir: `local_assets/reports/smoke/camera_reward_debug_autoloop_20260530_234454`.

## 2. Gates

- Gate A, 1-sample Fast inference: passed earlier.
- Gate B, 3 Fast rollouts: passed earlier.
- Gate C, camera condition: not proven.
- Gate D, reward-on-rollout: failed / not reliable.
- Gate E, VideoGPA encode: not allowed.
- Gate F, DPO: not allowed.

## 3. Camera Path Audit

`poses.npy` and converted `intrinsics.npy` do enter LingBot-Fast through `action_path`. Remote source audit of `wan/image2video_fast.py` shows `action_path` reads `poses.npy` and `intrinsics.npy`, builds `c2ws_plucker_emb`, and passes it into the Fast DiT. `wan/modules/model_fast.py` injects `c2ws_plucker_emb`.

Dummy `action.npy` stays zero and `use_action=false`. In non-`act` mode, LingBot reads `action.npy` only as compatibility baggage and does not use real action following.

## 4. Runtime Condition Debug

Condition debug JSON was written for attempted variants:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke/physion_movingcam_07abddf5748b/*/physion_movingcam_07abddf5748b/condition_debug.json
```

Observed:

- `poses_input_shape`: `[81, 4, 4]`
- raw intrinsics: `[81, 4, 4]`
- converted intrinsics: `[81, 4]`
- action: `[81, 4]`, norm `0.0`
- pipeline signature includes `action_path`
- direct Plucker embedding tensor was not hooked yet

## 5. Strong Camera Ablation

Attempted variants:

```text
repeat_correct_A repeat_correct_B correct frozen reversed exaggerated_yaw
```

The 480x832 attempt timed out under GPU contention. A fallback 256x448 / 4-frame run completed the command, but only `correct` produced a video:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke/physion_movingcam_07abddf5748b/correct/physion_movingcam_07abddf5748b/generated.mp4
```

Because repeat/camera variants did not all generate, stochastic baseline and correct-vs-frozen/reversed/exaggerated visual metrics could not be computed. Camera effect remains not proven.

## 6. Reward Failure Analysis

Original reward:

- Clean avg: `0.5949`
- Fast avg: `0.8796`
- Clean > Fast: `0.0`

After confidence-aware aggregation:

- Clean avg confidence-weighted: `0.2173`
- Fast avg confidence-weighted: `0.2256`
- Clean > Fast confidence-weighted: `0.3333`

The absolute confidence-weighted scores are now low, which correctly reflects fallback/missing backends. Ranking is still not fixed. The main bad term is `R_phys` motion proxy, which favors Fast on all three samples. `R_quality` is not the driver. Clean GT is also over-penalized by the frame-diff `P_freeze` proxy on two samples.

## 7. Feature Backend Blockers

- DINOv2: missing checkpoint; fallback proxy only.
- V-JEPA / VideoMAE: V-JEPA-like file exists, but loader forward is not wired; VideoMAE absent.
- Optical flow: real RAFT/GMFlow/WAFT forward not wired.
- `score_video --require_feature_backend true`: backend requirement not met.

## 8. VideoGPA / DPO Decision

Next-round VideoGPA encode is not allowed yet because Gate C and Gate D are not reliable. DPO remains explicitly disallowed.

## 9. Next Minimal Action

1. Add a LingBot runtime hook around `get_plucker_embeddings` in `wan/image2video_fast.py` to dump `c2ws_plucker_emb` shape/norm and verify variant differences before generation.
2. Rerun at most `correct/frozen/reversed` after GPU 6/7 are free.
3. Replace `R_phys` motion proxy and `P_freeze` frame-diff proxy with ID/object-state/flow-aware logic.
4. Wire real DINO or V-JEPA feature forward and real optical flow before trusting reward for pair selection.
