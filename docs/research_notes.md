# Research Notes

## LingBot / LingBot-World

- LingBot is relevant because the task is I2V/V2V world generation conditioned on image or prefix context.
- LingBot-Base is useful as a stronger teacher and branch-style baseline.
- LingBot-Fast is the target policy because the project optimizes a fast rollout model.
- The project does not require real action conditioning; camera poses and intrinsics are the active control signals.
- Fast checkpoint layout can differ from Base branch layout, so loaders must audit before training.

## GeoFlow

- Key idea: generated video should satisfy geometric consistency.
- For static background, motion should be explainable by camera-induced rigid flow.
- Foreground objects can move independently but should preserve identity and appearance.
- GeoFlow-style reward motivates `R_bg`, `R_cam`, and debug residuals.
- Difference: this project has known Physion/TDW camera pose, projection/intrinsics, depth, and ID masks for many samples.

## VideoREPA

- TRD distills spatial and temporal token relations from video representation encoders.
- It can improve physical temporal representation.
- It is an auxiliary loss, not a replacement for known-camera geometry reward.
- Hard representation matching alone does not guarantee camera following or reobserve consistency.

## V-JEPA / V-JEPA2

- Observation-only video representation learning supports action-free physical understanding.
- This supports the decision not to force an action signal.
- V-JEPA2 is used as a candidate TRD teacher when local weights are available.

## VideoGPA

- Preference alignment can improve video generation with geometry-aware preferences.
- This project differs by using I2V/V2V Physion camera conditions, simulator metadata, physical foreground rewards, and reobserve splits.

## Project Takeaway

Ordinary likelihood training does not explicitly optimize persistent world consistency. Physion-Cam-PhysGeo-DPO uses simulator-grounded camera/depth/ID/object-state signals to build rewards, corrupted negatives, and anchored DPO pairs.
