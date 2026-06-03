# Final Report: TDW Generation v2 PRD

## PRD

Path: `docs/PRD_physion_tdw_camphysgeo_dpo.md`.

It records weekly gates, smoke results, reward v5, DPO plumbing, video observations, terminology corrections, and TDW generation v2 requirements.

## Video Deliverables

Path: `local_assets/reports/tdw_video_deliverables/`.

The deliverables include an index and gallery for existing Physion/TDW clean GT, LingBot-Fast generated video, camera ablation videos, and reward contact sheets. No videos are committed to Git.

## Terminology

Physion is TDW / ThreeDWorld simulation, not real-world data. Current moving-camera data is Physion-style TDW moving-camera clean GT.

## Existing Video Issue

The old clean GT presentation sample has strong camera motion and foreground disappearance. It should be used as stress/test material, not warmup main data.

## Generation v2 Spec

Profiles defined:

- `warmup_mild`;
- `train_moderate`;
- `stress_reobserve`;
- `camera_only_static`.

Filtering includes target visibility, target area, disappearance length, camera magnitude/jerk, HDF5 key completeness, frame count, and metadata availability.

## Generation Result

- Stage 0 plan: supported.
- 1 sample: blocked before actual generation because existing upstream batch runner has no explicit mild-only camera set.
- 10 samples: skipped, gated on 1-sample success.
- 50 samples: planned, not run.

No large TDW generation was run.

## DPO Status

DPO engineering gates have passed up to 1-pair mini-loop, but signal sensitivity remains weak. No real training, no 5-pair overfit, and no VideoGPA 03_train were run.

## Next Actions

1. Add or expose mild-only camera variant support in the upstream moving-camera runner.
2. Run 1 -> 10 -> 50 TDW generation validation.
3. Use accepted `warmup_mild` samples for later LingBot-Fast camera warmup.
4. After enough data exists, use reward to select top/bottom DPO pairs.
5. Full generation and real training require user confirmation.

## Git

Branch: `physion-tdw-generation-v2-prd`.

Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`.

`local_assets` outputs, videos, HDF5, weights, latents, and logs are not committed.
