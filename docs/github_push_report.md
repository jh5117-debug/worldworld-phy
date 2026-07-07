Current Status: PASS

# GitHub Push Report Update

Updated: 2026-07-05 11:21:55

Documenting v12d final scheduler result: Job1 completed but failed training signal because final winner improvement was negative. Commit includes docs only; generated checkpoints/videos/local_assets/logs are not staged.

Current Status: PASS

# GitHub Push Report Update

Updated: 2026-07-05 10:49:58

Latest v12d commits pushed on `research/quant-small-lora-dpo-probe-20260624`:

- `2bd0c08 Prepare gated GPU scheduler for DPO v12d PRD`
- `f6d02c1 Implement GPU4-7 DPO scheduler and gate checks`

Scheduler launched in tmux session `dpo_gpu_scheduler_v12d`; Job1 is running on physical GPU4 only. No videos/images/local_assets/checkpoints/weights were staged in these commits.

Current Status: PASS

# GitHub Push Report Update

Updated: 2026-07-04 12:45:00

Latest pushed commits on `research/quant-small-lora-dpo-probe-20260624`:

- `59ff5d7 Prepare repaired ready500 manifest and metric backend verification PRD`
- `cf02804 Freeze repaired ready500 manifest as canonical`
- `e8ee278 Verify repaired ready500 metric backends`

Push status: PASS.

Canonical repaired manifest: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
Repaired splits: train400 / val50 / test50 / top50 demo regenerated from the repaired manifest.
Metric backend verification: LPIPS real smoke PASS; VBench real smoke PASS for temporal_flickering; FVD real I3D smoke PASS with scope caveat.

Large-file safety: no MP4/JPG/PNG/local_assets/checkpoints/weights were included in the pushed commits.

Current Status: PASS

# GitHub Push Report Update

Updated: 2026-07-04 04:17:06

Latest commit pushed: `40992cf Repair ready500 manifest after loser quality audit`

Push status: PASS on `research/quant-small-lora-dpo-probe-20260624`.

Large-file safety: no MP4/JPG/PNG/local_assets/checkpoints/weights were included in the commit.

Current Status: PASS

# GitHub Push Report Update

Updated: 2026-07-04 04:13:25

Latest commit pushed: `2a885c7 Audit ready500 loser quality and repair metric backends`

Push status: PASS on `research/quant-small-lora-dpo-probe-20260624`.

Large-file safety: no MP4/JPG/PNG/local_assets/checkpoints/weights were included in the commit.

Current Status: PENDING_PUSH

# GitHub Push Report Update

Updated: 2026-07-04 04:10:15

Pending commit for v11 loser quality audit and metrics backend repair.

<!-- DPO_PAIR_FACTORY_V11_PUSH:START -->
## DPO Pair Factory v11 Scale-500

- Scope: docs, source/tests, manifest JSONL, CSV/JSON/MD summaries.
- Excluded: MP4/JPG/PNG/contact sheet images/local_assets/checkpoints/weights.
- Ready500 manifest: `manifests/dpo_pair_factory_v11_ready_500.jsonl`.
<!-- DPO_PAIR_FACTORY_V11_PUSH:END -->

<!-- DPO_PAIR_FACTORY_V10B_PUSH:START -->
## DPO Pair Factory v10b Final Audit

- Commit scope: docs, audit script/tests, small CSV/JSON/JSONL manifests, data card, slide notes.
- Excluded: MP4/JPG/PNG/local_assets/checkpoints/weights/large logs.
- Ready pairs: 81.
- Top50 manifest: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`.
<!-- DPO_PAIR_FACTORY_V10B_PUSH:END -->

# GitHub Push Report: v8n tiny objective diagnosis

Current Status:
V8N_BLOCKED_WINNER_ANCHOR_REPEAT_SIGNAL_FAIL

Commits pushed in this phase include the v8n PRD, pair-cache objective selector/runner, default config fix, and result documentation. Large files, videos, images, checkpoints, and local_assets were not staged for push.


<!-- V8M_GIT:START -->
## v8m Git Checkpoint

Built and validated reviewed pair cache v8m. Commit pending at generation time. Cache tensors remain under `local_assets/` and are not staged.
<!-- V8M_GIT:END -->

<!-- V8L_GIT:START -->
## v8l Git Checkpoint

Prepared v8l objective preflight. Decision: `V8L_BLOCKED_WINNER_ONLY_CACHE_NO_LOSER_ENERGY`. Commit pending at generation time.
<!-- V8L_GIT:END -->

Current Status Update (2026-07-03T09:42:30): V8K_RESULTS_PENDING_COMMIT

v8k cache-only winner-anchor PASS; preparing docs/small CSV/log commit. No checkpoint/video/weights are staged.

Current Status Update (2026-07-03T09:16:56): V8K_PRD_PENDING_COMMIT

v8k cache-only winner-anchor PRD/status prepared. No winner-anchor run has started yet in this commit.

Current Status Update (2026-07-03T09:15:05): V8J_RESULTS_PENDING_COMMIT

v8j cache10 build+validation PASS; preparing source/docs/small reports commit. Cache tensors in local_assets are not staged.

Current Status Update (2026-07-03T08:50:49): V8J_PRD_PENDING_COMMIT

v8j cache10 build+validation PRD/status prepared. No runtime cache build has started yet in this commit.

Current Status Update (2026-07-03T08:48:33): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-03T08:48:18): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-03T08:47:32): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-02 22:03:10): V8G_COMMIT_READY_FOR_PUSH

- v8g result commit: `bef97c7` (`Run Wan from_pretrained split diagnosis v8g`).
- Branch: `research/quant-small-lora-dpo-probe-20260624`.
- Large files excluded: MP4/JPG/PNG/local_assets/checkpoints/weights.
- Next action: push current branch and verify remote head.

Current Status Update (2026-07-02 21:58:17): V8G_RESULTS_PENDING_COMMIT

v8g results are being prepared for commit/push. Large files, videos, images, checkpoints, and local_assets remain excluded.

Current Status:
V8F_PUSHED

# GitHub Push Report

Updated: 2026-07-02 19:31 CST

v8f PRD commit `9ab511a`, instrumentation commit `ababbb6`, and result commit `ae6b197` were pushed to `origin/research/quant-small-lora-dpo-probe-20260624`.

The v8f result commit includes docs, source/test update, small JSONL/markdown/CSV reports, and no videos/images/checkpoints/weights. Forbidden large artifacts were not added.


## v8h Update - 2026-07-03T06:46:04

Prepared v8h PRD in commit `815588e`. Added safe Wan policy loader instrumentation and v8h runtime/cache reports locally; final code/report commit pending after verification. No media/checkpoint/weights intended for commit.


<!-- dpo_pair_factory_v10_update -->
## DPO Pair Factory v10 Update

Current Status: PAIR_FACTORY_V10_READY_50_SYNTHETIC_MIXED

- Runnable prefix5 conditions recovered: 102.
- Existing strict DPO-ready pairs: 18.
- Synthetic visible TypeM-v10 ready pairs: 63.
- Combined ready pairs: 81.
- Combined manifest: `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`.
- Caveat: 63 new pairs are controlled synthetic visible negatives, not true rollout TypeB losers.
- No DPO / SDPO / Linear-DPO / StageA / StageB / GRPO / broad-LoRA was run.
<!-- /dpo_pair_factory_v10_update -->

## DPO Training Sanity v12

- Prepared PRD/subsets/scope inventory and pushed commits through scope sanity.
- Added checkpoint saving to cache objective runner.
- Tiny S1 strict SDPO stopped at step10 with `DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`.
- No media/checkpoints/local_assets staged or pushed.

<!-- V12B_OBJECTIVE_REPAIR_PUSH_NOTE_START -->

## V12B OBJECTIVE REPAIR PUSH NOTE

Prepared v12b reports and lightweight CSV/JSON summaries for commit/push. No media, cache tensors, checkpoint tensors, or weights are staged.

<!-- V12B_OBJECTIVE_REPAIR_PUSH_NOTE_END -->

<!-- V12C_PUSH_NOTE_START -->

## V12C PUSH NOTE

v12c PRD/setup/code/report are pushed as lightweight files only. No local_assets, media, checkpoint, tensor, or weight files were pushed.

<!-- V12C_PUSH_NOTE_END -->

## 2026-07-05 StageA V2V-5 Warmup 4900x2 Data Gate

Prepared a strict 4900 train / 100 test StageA V2V-5 warmup gate and GPU4-7 launcher. The gate found only 3299 unique Stage1-ready clips on disk, so the requested 4900/100 warmup was not launched. Added `PYTHONNOUSERSITE=1` to the launcher to avoid the current user-site Python initialization hang.

## 2026-07-06 Full-data Warmup Loser Source Smoke

- Added safe Wan from_pretrained option for V2V-5 inference.
- Ran 2-condition smoke for `fulldata-lingbotfast-warmup-weights`.
- Decision: not better than old C on first 2 reviewed conditions; 500 generation not launched.
- Cleanup inventory written; no data/weights/checkpoints deleted.


## 2026-07-06 Full-data Warmup Checkpoint Selection Smoke

- Tested intermediate checkpoints `step_000103`, `step_000206`, `step_000309`, and `step_000412` on H20 GPU4-7.
- Each produced one reviewed `01002` contact sheet/future video.
- Codex visual decision: no clear improvement over old C; not suitable to scale to 500 videos.
- The smoke runner stalled before completing `01008`; own smoke processes were terminated and GPU4-7 freed.
- No DPO, StageA/StageB/GRPO, checkpoint deletion, or media/weights push.


## 2026-07-06 Safe Cleanup After Full-data Warmup Gate

- Deleted failed full-data warmup loser-eval transient local media only: 54M total.
- Wrote large cleanup candidate manifest requiring explicit approval before deleting checkpoint/data/weight lineage.
- No ready500 assets, old C reference adapters, checkpoints, raw data, or weights were deleted.


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


## Old Weight/Rollout Cleanup Update - 2026-07-06 10:45 CST

Deleted old non-current experiment checkpoint/adapter directories and rollout media:

- Jun-22 `fast_stageA_high_only_data_gate_20260622_135505` checkpoint directories after optimizer states were already removed.
- Old `overnight_quant_lora_dpo_20260624_overnight_test` rollout/media package.

Freed approximately 9.7G more. Repo `local_assets` is now about 16G; `/home/nvme04` available space is about 345G.

Deletion evidence:

- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_deleted_manifest.csv`
- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_deleted_manifest.md`
- `reports/cleanup_fulldata_warmup_loser_eval/old_weight_rollout_delete_verify.txt`

Still kept:

- current `fulldata-lingbotfast-warmup-weights`
- old C reference sweep `local_assets/experiments/small_lora_scope_sweep_20260624`
- ready500 / v11 pair-factory assets
- raw Physion/local condition data


## PRD Maintenance Update - 2026-07-06 10:47 CST

Added `docs/experiments/PRD_MAINTENANCE_INDEX.md` to separate active PRDs from superseded/historical PRDs. Historical PRD markdown files are retained because they are small and preserve experiment provenance; large generated artifacts and non-current weight/cache directories were cleaned instead.

## 2026-07-06 11:05 CST - Fulldata loser-source cleanup follow-up

- Stopped stale `dpo_gpu_scheduler_v12d` after its tiny-DPO training gate had failed; current objective is loser-source evaluation / cleanup, not DPO training.
- Added current remaining asset audit under `reports/cleanup_fulldata_warmup_loser_eval/`.
- Updated PRD maintenance index and fulldata warmup loser-source status.
- No media, checkpoints, weights, or `local_assets/` pushed.

## 2026-07-06 11:12 CST - Additional stale media cleanup

- Removed additional old superseded local media/cache directories from `local_assets/`, including v10 media, old StageA v2v5 outputs, targeted BC local rollout media, early DPO protocol media, and old V2V5 rollout media.
- `local_assets` reduced to about 11G; `/home/nvme04` free space increased to about 350G.
- Preserved current fulldata warmup weights, old C reference, v11 ready500 media, raw Physion/local data, and v12b repair lineage.
- No media, checkpoints, weights, or `local_assets/` pushed.

## v13b Objective Search Implementation

- Updated: 2026-07-06T13:08:17+08:00.
- Prepared v13b GPU4/5-only objective search code and reports.
- Training blocked by GPU4/5 occupancy; no large assets staged.
## v13b Objective Search Push Note

Prepared v13b objective-search summaries and decision docs for push. Only lightweight docs, CSV, JSON, and logs are included. Large artifacts, videos, images, local_assets, checkpoints, and weights are excluded.

## v14 Utility Calibration Push

- Prepared and ran v14 pair inventory, beta/loss response, latent backend audit, and normalization design.
- Real all500 LingBot energy remains blocked by 1-pair runtime initialization timeout; no fake energy values were committed.
- Committed only lightweight docs/source/tests/manifests/CSV/JSON summaries.
- Did not push local_assets, videos, images, checkpoints, weights, HDF5/NPY/NPZ/PT/PTH/safetensors, or large logs.

## v14 Objective Runner Scaffold Push

Added a calibrated v14 objective wrapper and log-normalized winner-detached objective support. No training was launched and no checkpoint/video/local_assets files were pushed.

## v14 E02 Smoke10 Push

Committed only lightweight E02 smoke CSV/summary and docs. Did not push local checkpoint files, local_assets, videos, images, or weights.

## v14 E03 Smoke10 Push

Committed lightweight E03 partial CSV/summary only. The own E03 process was stopped after winner-worse gate failure. No checkpoint/video/local_assets files were pushed.


## v14 E02_best7 Video Audit Update (2026-07-07T02:37:56.080956Z)

Prepared lightweight audit/docs for E02_best7. Large local assets, videos, contact-sheet images, and checkpoints are intentionally not staged or pushed.

## v14 Objective Search Update (2026-07-07T03:56:37.931118Z)

- Added E04_screen5 and E05_screen5 screening runs on physical GPU4/GPU5 only.
- E04_screen5 (`no_lose_gap_normalized_win_only`) training signal PASS: mean winner improvement `0.00012879371643066407`, final `0.00013786554336547852`, WCR `0.7916`, loser degradation negative.
- E05_screen5 (`normalized_clipped_loser`, alpha_l=0.02) training signal PASS: mean winner improvement `0.00012555122375488282`, final `0.00012230873107910156`, WCR `0.8220`, slight loser degradation.
- E04 checkpoint videos generated: `8` true V2V-5 videos. Codex visual audit FAIL: step005 worsens object count/identity in multiple samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400.

## v14 E05 Audit Push (2026-07-07T05:04:09.871964Z)

Prepared lightweight report updates for E05 checkpoint metrics and Codex visual audit. No local_assets, videos, images, checkpoints, or weights are intended for commit.

## v14 E01/E06 Screen Push (2026-07-07T06:06:00.444732Z)

Prepared lightweight report updates for E01/E06 20-step training signal and E06 checkpoint eval blocker. No local_assets, videos, images, checkpoints, or weights are intended for commit.


## v14 DPO Objective Search Visual Gate Decision Push (2026-07-07T18:02:47Z)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Commit pushed: `2f38301` (`Document v14 DPO objective search visual gate failures`)
- Decision: `DPO_RECIPE_NOT_FOUND_V14`
- Summary: E09 and E10 had healthy scalar/gap training signals but failed true V2V-5 visual gates; no S16/S32/train400/large DPO is allowed from these recipes.
- Pushed artifacts: lightweight docs, CSV/JSON/MD summaries, fixed validation manifests, and Codex video audit CSV/MD.
- Not pushed: local_assets, MP4/JPG/PNG/contact sheets, checkpoints, weights, safetensors, NPY/NPZ/HDF5, and large logs.
- GPU constraint respected for v14 documented jobs: only H20 physical GPU4/GPU5 were used; GPU0-3/6/7 were not used by these v14 objective-search jobs.

## v14 Requirement Audit Push (2026-07-07T18:12:56Z)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Commit pushed: `84bd863` (`Add v14 requirement audit and blocker evidence`)
- Added audit: `reports/dpo_utility_calibration_v14/requirement_audit.md` and `.json`.
- Clarified blockers: all500 energy rows are `MISSING_REAL_ENERGY`; latent monitor is `LATENT_MONITOR_BLOCKED`; E09/E10 remain scalar-signal-only with visual gate failures.
- Scale permission remains `NO_SCALE`; train400 remains blocked.
- No local_assets, videos, images, checkpoints, weights, or large logs were pushed.

## v14 Scheduler Artifact Push (2026-07-07T18:26:25Z)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Commit pushed: `62c44e2` (`Add conservative GPU scheduler artifact for v14`)
- Added conservative GPU4/5-only scheduler artifact: `cam_physgeo/orchestration/gpu_scheduler_v14.py`, `scripts/launch_dpo_v14_scheduler.sh`, and `tests/test_gpu_scheduler_v14.py`.
- Scheduler smoke wrote `reports/dpo_utility_calibration_v14/scheduler_state.json` with `scheduler_decision=NO_TRAINING_NO_SCALE` and no training command after `DPO_RECIPE_NOT_FOUND_V14`.
- No videos, images, checkpoints, weights, local_assets, or large logs were pushed.

## v14 Blocker Retry Plan Push (2026-07-07T18:31:36Z)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Commit pushed: `972ab38` (`Add v14 blocker retry plan`)
- Added dry-run blocker retry plan: `reports/dpo_utility_calibration_v14/blocker_resolution_plan.md`, `configs/cam_physgeo/dpo_v14_blocker_retry.yaml`, and `scripts/plan_v14_blocker_retry.sh`.
- Added direct import smoke summary: `reports/dpo_utility_calibration_v14/direct_import_smoke_v14.md`.
- The retry script defaults to dry-run and requires `RUN_V14_BLOCKER_RETRY=1` plus GPU4/5 only before execution.
- No training, rollout, checkpoint deletion, videos/images/weights/local_assets push, train400, or large DPO was performed.

## v14 Real-Energy Blocker Retry Pending Push

Prepared lightweight v14 blocker retry summaries. No local_assets videos, checkpoints, weights, or raw large logs should be staged.
