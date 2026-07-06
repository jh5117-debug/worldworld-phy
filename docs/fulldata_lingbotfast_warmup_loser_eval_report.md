# Full-data LingBotFast Warmup Loser Eval Report

## Result

`fulldata-lingbotfast-warmup-weights` is runnable with the safe loader patch, but the 2-condition visual and metric smoke does not show it is better than the previous small-step C loser source.

## Evidence

Visual review:

- `01002_drop_orbit_left_72_seed40002`: new C and old C are very similar. Both produce clear frames but miss the red/green sphere physical event and reobserve/collision behavior.
- `01008_drop_orbit_left_72_seed40008`: new C has visible object disappearance/duplicate green fragments. Old C has a similar failure with slightly fewer fragments.

Metrics sampled every 10 frames:

- `01002`: new vs GT PSNR 14.450, old vs GT PSNR 14.431; SSIM new 0.637, old 0.641.
- `01008`: new vs GT PSNR 14.576, old vs GT PSNR 14.605; SSIM new 0.300, old 0.307.

Interpretation: no convincing improvement; second sample is marginally worse by SSIM and visual artifacts.

## Decision

Do not use GPU4-7 to generate 500 videos from this final adapter yet. Recommended next step is to compare checkpoint candidates (`step_000103`, `step_000206`, `step_000309`, `step_000412`, `final`) on an 8/16-condition smoke and select the best loser source before scaling.

## Cleanup Inventory

Repo-local storage summary:

- `local_assets`: about 58G
- `reports`: about 943M
- largest candidate areas include `local_assets/dpo_training_sanity_v12`, `local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505`, old pair caches, and old objective caches.

No cleanup deletion was performed because “unused” artifacts include checkpoints/adapters and generated data that may still be referenced by manifests or reports.


## Checkpoint Selection Follow-up - 2026-07-06 10:26 CST

After the final adapter failed the initial 2-condition gate, four intermediate full-data warmup checkpoints were tried on GPU4-7: `step_000103`, `step_000206`, `step_000309`, and `step_000412`.

Outcome:

- 4/4 checkpoints generated a contact sheet for `01002_drop_orbit_left_72_seed40002`.
- Visual review found the same failure family as old C: readable video, but missing physical response and late object-fragment artifacts.
- No checkpoint showed a clear quality/usefulness improvement over old C.
- The multi-condition smoke did not advance cleanly to `01008`; it stalled after the first generated sample, so the smoke jobs were stopped.

Decision remains: do not generate 500 DPO loser videos from `fulldata-lingbotfast-warmup-weights` yet.


## Cleanup Follow-up - 2026-07-06 10:35 CST

Removed only failed-eval transient local media:

- `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_checkpoint_select` (33M)
- `local_assets/dpo_pair_factory_v11/new_c_warmup_loser_smoke` (21M)

Potential large reclaim candidates are documented but not deleted because they may contain checkpoints, pair-factory data, old C references, or ready500 assets. See `reports/cleanup_fulldata_warmup_loser_eval/large_cleanup_candidates_requires_approval.md`.


## Cache-Only Cleanup Update - 2026-07-06 10:38 CST

Deleted old regenerated cache tensor directories only:

- `local_assets/dpo_pair_cache_v8m` (3.0G)
- `local_assets/dpo_objective_cache_v8j` (1.4G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49` (2.2G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49_retry2` (2.2G)
- `local_assets/dpo_training_sanity_v12/scope_sanity_cache_s0_window49_retry4` (4.3G)
- `local_assets/dpo_objective_cache_v8i` (271M)
- `local_assets/dpo_objective_cache_v8d` (12K)

Freed approximately 13G. `/home/nvme04` available space increased to about 316G.

Deletion manifest:

- `reports/cleanup_fulldata_warmup_loser_eval/cache_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/cache_deleted_manifest.md`

No raw data, model weights, adapters/checkpoints, ready500 assets, old C reference assets, or full-data warmup weights were deleted.


## Old Experiment State Cleanup - 2026-07-06 10:43 CST

Deleted additional old experiment artifacts:

- Old Jun-22 StageA data-gate optimizer `training_state.pt` files only, leaving adapter states/manifests/log lineage in place.
- Failed v12 strict-SDPO regenerated latent cache `local_assets/dpo_training_sanity_v12/guarded_sdpo_anchor_s1/cache_s1_window49_run1`.

Freed approximately 20G more. Repo `local_assets` is now about 25G; `/home/nvme04` available space is about 336G.

Deletion evidence:

- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_deleted_manifest.md`
- `reports/cleanup_fulldata_warmup_loser_eval/old_experiment_delete_verify.txt`

Kept:

- current `fulldata-lingbotfast-warmup-weights`
- old C reference adapter assets
- ready500 / pair-factory dataset assets
- raw Physion/local condition data
- adapter_state files from the old StageA gate
