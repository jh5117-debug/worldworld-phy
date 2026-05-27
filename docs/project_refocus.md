# Physion-Cam-PhysGeo-DPO Refocus

We no longer define this project as CSGO/action-data fine-tuning for LingBot, and we no longer use PhyInOne as the active data line. The current negative results show that ordinary SFT, even on physical videos, does not explicitly optimize persistent world consistency. It can still produce background drift, object deformation, camera mismatch, and reobserve failure.

The project is now Physion-Cam-PhysGeo-DPO: camera-conditioned physical-geometric preference alignment for LingBot-Base and LingBot-Fast.

Given an initial image or prefix video, prompt, camera poses, and intrinsics, LingBot should generate a persistent physical world. The static background should follow the rigid geometry induced by the provided camera trajectory. Dynamic foreground objects should preserve identity and shape. Physical events should remain plausible for drop, collision, roll, containment, support, dominoes, drape, and link scenarios. When the camera turns away and comes back, the scene and objects should remain consistent. The model should not win by freezing, blurring, or suppressing motion.

Data is Physion-only:

- Official Physion is used for static-camera physical dynamics, object states, depth, segmentation, flow when available, and event labels.
- Existing Physion/TDW moving-camera data is used for camera-conditioned reward, reobserve evaluation, corrupted negatives, and anchored DPO.
- If official Physion HDF5 lacks camera intrinsics/extrinsics, the TDW/Physion generation code should be rerun for a subset with exported `camera_position`, `camera_aim`, `camera_pose`, `projection_matrix`, depth, ID mask, and object states.

Methodologically, we borrow GeoFlow's geometry reward idea but do not copy its setting. GeoFlow estimates camera/depth/flow inside a T2V setup. Here, the Physion/TDW setting provides simulator camera pose, projection/intrinsics, depth, ID masks, and object metadata, so the reward is known-camera and simulator-grounded.

We also borrow VideoREPA-style TRD as an auxiliary temporal-physical representation loss. TRD is not the main camera-following or reobserve objective.

Training uses bootstrapped anchored DPO. We do not start with pure self-rollout DPO because LingBot-Fast can initially produce low-quality Physion-domain rollouts. The first preference pairs are anchored by clean Physion GT, corrupted negatives, and later teacher/base rollouts; self-rollout DPO is gated until pass@K and quality are acceptable.

Innovation points:

- Shift from action/game world modeling to Physion-based camera-conditioned physical world consistency.
- Use Physion/TDW HDF5 camera/depth/ID/object-state signals for training and evaluation.
- Convert GeoFlow-style reward into a known-camera simulator-grounded reward.
- Add physical event and reobserve consistency rewards.
- Use ID-mask and video-space corrupted negatives.
- Use bootstrapped anchored DPO before self-rollout DPO.
- Build an I2V/V2V Physion camera-conditioned benchmark for LingBot.
