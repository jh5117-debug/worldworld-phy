# Final Report: Plucker / Reward Backend Debug

## 1. Current Gates

- Gate A, LingBot-Fast 1-sample actual inference: passed.
- Gate B, 3 Fast rollouts: passed at smoke level.
- Gate C, camera condition effect: partial. Camera condition reaches and changes LingBot's Plucker/control tensor, but video-level effect is still not proven above stochastic baseline.
- Gate D, reward-on-rollout: failed / not reliable. V2 aggregation makes this failure explicit by marking proxy-only confidence.
- Gate E, VideoGPA encode: not allowed.
- Gate F, DPO: not allowed.

## 2. Plucker / Camera Embedding Probe

Probe script: `cam_physgeo/eval/probe_camera_embedding.py`.

Run output:

- `local_assets/reports/smoke/camera_embedding_probe/summary.json`
- `local_assets/reports/smoke/camera_embedding_probe/pairwise_distances.csv`

The probe calls LingBot's actual camera utility path without full generation:

- `wan.utils.cam_utils.get_Ks_transformed`
- `interpolate_camera_poses`
- `compute_relative_poses`
- `get_plucker_embeddings`

Sample `physion_movingcam_07abddf5748b`:

- Poses: `(81, 4, 4)`
- Raw intrinsics: `(81, 4, 4)`
- Converted intrinsics: `(81, 4)`
- Dummy action: `(81, 4)`, norm `0.0`
- Rearranged Plucker tensor: `(1, 192, 2, 8, 14)`
- Dummy action tensor: `(1, 256, 2, 8, 14)`
- Final LingBot control tensor: `(1, 448, 2, 8, 14)`

Pairwise camera-control distances:

- correct vs frozen: L2 `12.8458`, cosine `0.994244`
- correct vs reversed: L2 `25.6122`, cosine `0.977121`
- correct vs exaggerated_yaw: L2 `83.0763`, cosine `0.759289`
- correct vs zero_motion: L2 `12.8458`, cosine `0.994244`
- frozen vs zero_motion: L2 `0.0`

Conclusion: camera variants change the actual LingBot control tensor. If video outputs still look similar, the likely issues are model sensitivity, sampling/seed variance, short generation length, or downstream DiT usage strength, not failure to construct Plucker embeddings.

## 3. Video-Level Camera Effect

No new video-level ablation was run in this round. GPU 6/7 were heavily occupied, and the previous strong ablation had already hit OOM/timeout pressure. This round only proves embedding-level camera differences.

Gate C remains partial:

- Path and embedding: confirmed.
- Visible generation effect: not proven.

Next camera-only action: rerun one same-seed 4-frame 256x448 ablation after GPU 6/7 are free, comparing repeat-correct baseline against frozen and exaggerated-yaw variants.

## 4. Reward Input Audit

Probe script: `cam_physgeo/eval/audit_reward_inputs.py`.

Run output:

- `local_assets/reports/smoke/reward_input_audit/summary.json`
- `local_assets/reports/smoke/reward_input_audit/reward_input_audit.jsonl`
- `local_assets/reports/smoke/reward_input_audit/backend_table.csv`

Findings for the three rollout samples:

- Clean GT metadata exists and includes real Physion-side signals such as depth/id/camera availability.
- Fast generated rollouts do not have generated depth/id outputs.
- The current reward implementation still marks every clean and Fast component as fallback.
- Clean GT therefore does not get real-backend credit from depth/id/camera/object-state yet.

This explains why Fast can score above clean: the scorer is still comparing proxy motion/quality terms rather than simulator-grounded clean metadata.

## 5. Reward Aggregation V2

Changed files:

- `cam_physgeo/rewards/total_reward.py`
- `cam_physgeo/eval/eval_fast_rollouts.py`

New/strengthened outputs:

- `R_total_raw`
- `R_total_no_quality`
- `R_total_confidence_weighted`
- `R_total_real_backend_only`
- `R_total_proxy_only`
- `R_geometry_only`
- `R_identity_only`
- `R_motion_only`
- `R_quality_only`
- `P_freeze`

Aggregation rules now enforce:

- `backend="missing"` => confidence `0`.
- `backend="fallback"` => confidence <= `0.25`.
- confidence-weighted `R_quality` weight <= `0.05`.
- fallback components cannot be reported as high-confidence wins.

V2 rollout scores:

- Raw clean avg: `0.5949391852320083`
- Raw Fast avg: `0.8796054208438063`
- Raw clean > Fast win rate: `0.0`
- Confidence-weighted clean avg: `0.19335628899522198`
- Confidence-weighted Fast avg: `0.2175242075449916`
- Confidence-weighted clean > Fast win rate: `0.0`
- Real-backend-only clean avg: `0.0`
- Real-backend-only Fast avg: `0.0`
- Proxy-only clean avg: `0.7810828307925798`
- Proxy-only Fast avg: `0.8787116502807581`

Interpretation:

- The reverse ranking is still present in proxy totals.
- The new real-backend-only score correctly exposes that no trusted backend is active.
- Current reward is still not usable for DPO pair selection.

## 6. Feature Backend Plan

DINOv2:

- `local_assets/weights/dinov2` exists but file count is `0`.
- Load test: `fallback_proxy_only`.
- Needed for real `R_fg` and `R_reobs`.

V-JEPA / VideoMAE:

- `local_assets/weights/vjepa2` has one file, about `1.664 GB`.
- Load test: path present, not forwarded.
- Needed for temporal/reobserve features and optional TRD-style signals.

Optical flow:

- Assets exist under `local_assets/weights/optical_flow`, but reward code does not call RAFT/GMFlow/WAFT.
- Needed for `R_bg`, `R_cam`, and `P_freeze`.

No downloads were performed.

## 7. Allowed Next Steps

VideoGPA encode: no.

Reason: Gate C video-level camera effect is not proven, and Gate D reward remains proxy-only.

DPO: no.

Reason: real reward backends and DPO energy/logprob adapters are still absent.

Recommended next minimal action:

1. If prioritizing camera: run a tiny same-seed video ablation after GPU 6/7 are free.
2. If prioritizing reward: wire clean GT depth/id/camera/object-state into real `R_bg`, `R_cam`, `R_fg`, `R_phys`, and `P_freeze`.
3. If prioritizing backend readiness: add DINOv2 and optical-flow forward smoke before any pair selection.

No training, DPO, VideoGPA encode, Stage1, or large rollout was run in this round.
