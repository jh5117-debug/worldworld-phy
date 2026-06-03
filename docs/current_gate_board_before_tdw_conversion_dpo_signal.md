# Current Gate Board Before TDW Conversion + DPO Signal Finalize

Generated: 2026-06-04

Worktree used for remote validation:
`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work/world_model_phys_tdw_generation_v2_prd_work/world_model_phys_tdw_generation_v2_mild_smoke_work`

`local_assets` in that worktree is a symlink to the shared project assets tree. No assets, weights, HDF5, MP4, NPY, latents, or logs are staged for Git.

| Gate | Status | Evidence | Next Action |
|---|---|---|---|
| TDW 1-sample actual | passed | `0000.hdf5` exists for `00000_drop_orbit_left_12_seed10000`; profile `warmup_mild`; camera `orbit_left_12`; generated under the prior one-sample GPU0 approval. | No more TDW generation this round. |
| TDW HDF5 validation | passed | 83 frames; RGB/depth/id/camera pose/position/aim/projection/object state present; target_visible_ratio `1.0`; max invisible frames `0`; camera path length `0.5927`. | Keep as accepted warmup candidate. |
| TDW LingBot conversion | pending before this run | Previous conversion emitted arrays and metadata, but `target.mp4` probe had not been validated. | Force rewrite and probe `target.mp4`. |
| target.mp4 probe | pending before this run | Conversion produced file, remote probe incomplete. | Must pass before 10-sample request. |
| TDW 10-sample approval | blocked by approval | Current TDW display is GPU0-bound `DISPLAY=:8`; only one sample was approved and consumed. | Ask user before any GPU0 10-sample. |
| DPO signal fast runner | incomplete | Mode exists but previous run did not complete due SSH instability. | Run on GPU6/7 only. |
| 5-pair tiny overfit | no-go before this run | Signal gate incomplete. | Only write go/no-go, default no run. |
| Full TDW generation | no | 10/50 not validated. | Requires staged validation and user approval. |
| Real DPO training | no | Engineering gates are smoke-only; signal remains unresolved. | No training. |
