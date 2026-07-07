# DPO Utility Calibration v14 Status

Updated: 2026-07-08 01:50 CST

Decision: `DPO_RECIPE_NOT_FOUND_V14`

## Current State

- Canonical repaired ready500 remains the required data entry.
- Offline beta calibration found the prior DPO utility was under-scaled: `u_log` around 1e-4 requires beta around 1000, not beta=0.1.
- Calibrated objectives now produce real training-gap movement; the blocker has shifted from no-signal to visual degradation in true V2V-5 checkpoint rollouts.
- Only physical GPU4/GPU5 were used for v14 E09/E10 training/eval in this update. GPU0-3/6/7 were not used by these v14 jobs.

## Latest Objective Search Evidence

| Scheme | Training Signal | Video Gate | Decision |
|---|---:|---:|---|
| E07 linear winner detached | PASS at 200 steps | FAIL step200 worse 4/4 | not valid |
| E08 calibrated local/full log | PASS at 200 steps | NOT_RUN | training-signal only |
| E09 source weighted rollout priority | PASS early at step50 | FAIL step50 worse/not-better 4/4 | not valid |
| E10 L2 camera-temporal r4 | PASS at 100 steps | FAIL step100 worse 2/4, not clearly better on rest | not valid |

## Exact Current Blocker

The calibrated DPO/winner-anchor objectives can lower winner energy and avoid loser-dominant scalar metrics, but the LoRA updates still degrade generated videos with foreground duplication, object/fragment clutter, white/yellow line or text-like artifacts, and scene contamination.

## Scale Permission

- S16/S32: blocked.
- train400: blocked.
- large DPO: blocked.

Next work should add a rollout-quality/latent visual monitor or stronger visual regularization before further DPO scaling.


## v14 Final Test Status

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Targeted pytest suite: NOT RUN because `pytest` is unavailable in the active H20 shell. No pytest PASS is claimed.
- Test status path: `reports/dpo_utility_calibration_v14/test_status.md`.

## v14 Requirement Audit (2026-07-07T18:10:35Z)

- Requirement audit path: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14`.
- All500 energy CSVs are coverage/blocker files with `MISSING_REAL_ENERGY`, not real energy calibration evidence.
- Superseded latent-monitor status: later DINO/V-JEPA2 runs produced real margins; current status is `PASS_WITH_ASSET_BLOCKERS` with 74/74 positive V-JEPA2 token-relation margins among available videos.
- Best scalar candidates E09/E10 failed true V2V-5 visual gates, so S16/S32/train400 remain blocked.

## v14 Scheduler Artifact Update (2026-07-07T18:24:43Z)

- Added `cam_physgeo/orchestration/gpu_scheduler_v14.py`.
- Added `scripts/launch_dpo_v14_scheduler.sh`.
- Added `tests/test_gpu_scheduler_v14.py`.
- Smoke output path: `reports/dpo_utility_calibration_v14/scheduler_state.json` and `scheduler_state_summary.md`.
- Scheduler decision: `NO_TRAINING_NO_SCALE`; it records GPU/state evidence and does not launch training after `DPO_RECIPE_NOT_FOUND_V14`.

## v14 Blocker Retry Plan Update

- Added blocker resolution plan: `reports/dpo_utility_calibration_v14/blocker_resolution_plan.md`.
- Added conservative dry-run command generator: `scripts/plan_v14_blocker_retry.sh`.
- Added config: `configs/cam_physgeo/dpo_v14_blocker_retry.yaml`.
- Added direct import smoke log: `reports/dpo_utility_calibration_v14/test_logs/direct_import_smoke_v14.log`.
- These artifacts do not launch training and do not change `NO_SCALE`.

## v14 Real-Energy Blocker Retry Update

- Retry summary: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_retry_summary.md`.
- Original S_pass real-energy row failed because the v14 nested manifest did not satisfy `Prefix5DpoDataset` schema and old v6b rollout video assets were missing.
- A one-pair asset-complete prefix5 adapter was built from a synthetic controlled pair and passed schema validation.
- Conda Python 3.13 failed due transformers/huggingface-hub conflict; `/usr/bin/python3` imported the real energy stack successfully.
- The `/usr/bin/python3` retry loaded 16 LingBot shards and entered the VAE path, but timed out after 900 seconds before writing the first real-energy row.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400 remain blocked.

## v14 Real-Energy Stage Debug Update

- Stage debug path: `reports/dpo_utility_calibration_v14/blocker_retry/stage_debug/real_energy_stage_debug_summary.md`.
- The repaired asset-complete one-pair path passed schema/env/shard loading.
- `4_init_energy_runtime` completed but took about 557.6 seconds.
- `5_decode_example` completed in about 68.1 seconds.
- The run then timed out at `7_encode_winner_probe`; no real-energy row was produced.
- Current exact blocker: `REAL_ENERGY_STAGE_DEBUG_TIMEOUT_ENCODE_WINNER_PROBE`.
- DPO decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400 scale is allowed.

## v14 Real-Energy CUDA Runtime Update

- CUDA runtime summary: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_cuda_runtime_pass_summary.md`.
- The CPU runtime stage debug timed out at `7_encode_winner_probe`.
- Re-running the same asset-complete one-pair audit with `--runtime_device cuda` produced a real `status=ok` energy row.
- Energy seconds: `212.4425`; CUDA peak memory about `50.43GB`.
- This repairs the one-pair real-energy path but does not change the DPO recipe decision: `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400 remain blocked.

## v14 Bounded Real-Energy Calibration2 Update

- Summary: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration4_cuda_runtime_limit2/real_energy_calibration2_summary.md`.
- Adapter manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration4.jsonl` contains 4 schema-valid asset-complete TypeM-v11 synthetic pairs for calibration.
- Bounded run used physical GPU4 only with `--runtime_device cuda` and wrote 2/2 `status=ok` real energy rows.
- Energy seconds were about `228.92s` and `225.68s`; peak CUDA memory was about `50.43GB`.
- This proves the calibration path can move beyond one pair, but it is still too expensive for all500 without batching/cache improvements.
- DPO decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked.

## v14 Calibration4 Gap Scale Update

- Real-energy gap scale summary: `reports/dpo_utility_calibration_v14/real_energy_gap_scale_calibration4_summary.md`.
- Calibration4 now has 4/4 `status=ok` rows from real LingBot energy using GPU4/GPU5 with `--runtime_device cuda`.
- At policy=reference init, `reference_relative_margin` is exactly zero, so beta sweep correctly reports `NONE_ZERO_UTILITY`; beta cannot create DPO signal without a nonzero policy-reference utility change.
- Pair `Delta_ref` values were `[0.02072979509830475, 0.00031509879045188427, -8.203089237213135e-05, 0.008667878806591034]`, showing order-of-magnitude variation and one negative energy preference despite visual/reward labels.
- If training utility remains about `1e-4`, beta must be about `1000` to reach `beta*u ~= 0.1`; the old `beta=0.1` is effectively no-signal at that scale.
- DPO decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked.

## v14 Latent Monitor Backend Audit Update

- Backend audit: `reports/dpo_utility_calibration_v14/latent_monitor/backend_audit.md`.
- Updated audit now distinguishes local code files from actual local weight candidates.
- Local weight candidates found: VJEPA2 `vjepa2_1_vitb_dist_vitG_384.pt` and DINOv2 `dinov2_vits14_pretrain.pth`.
- Decision: `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING`, not PASS. No TRD/VJEPA margin values have been produced yet.
- No model download, no training, and no fake latent scores were produced.
- DPO decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked.


## v14 DINOv2 Frame Latent Monitor Smoke Update (2026-07-07T22:19:25Z)

- Smoke CSV: `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke.csv`.
- Smoke summary: `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke_summary.md`.
- Backend: local `dinov2_vits14_pretrain.pth` loaded through transformers `Dinov2Model` with an explicit key mapping; no download was attempted.
- Device: `CUDA_VISIBLE_DEVICES=4`, process `cuda:0` mapping to physical GPU4.
- Result: `LATENT_MONITOR_DINO_FRAME_SMOKE_PASS` on 4/4 asset-complete calibration pairs.
- Positive frame cosine margin rows: 4/4.
- Positive temporal-relation margin rows: 4/4.
- This is a real latent/visual monitor score, but it is a DINOv2 frame fallback smoke, not a full V-JEPA/TRD auxiliary-loss PASS.
- DPO decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked until a recipe passes true checkpoint video + metrics + Codex audit.


## v14 DINOv2 Latent Monitor Test Update (2026-07-07T22:20:16Z)

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Direct smoke for `tests/test_latent_relation_monitor_v14.py`: PASS for audit no-fake-values, code-only blocker, local weight detection, DINOv2 qkv mapping, and future-frame sampling.
- `pytest -q tests/test_latent_relation_monitor_v14.py`: NOT RUN because `pytest` is unavailable in the active H20 shell (`exit 127`). No pytest PASS is claimed.
- DINOv2 frame smoke: `LATENT_MONITOR_DINO_FRAME_SMOKE_PASS` with 4/4 ok rows.


## v14 V-JEPA2 Latent Monitor Smoke Update (2026-07-07T22:32:50Z)

- V-JEPA2 smoke CSV: `reports/dpo_utility_calibration_v14/latent_monitor/vjepa2_video_smoke.csv`.
- Required summary path: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`.
- Required monitor path: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`.
- Backend: local V-JEPA2.1 ViT-B EMA encoder from `vjepa2_1_vitb_dist_vitG_384.pt`; no model download.
- Device: `CUDA_VISIBLE_DEVICES=4`, process `cuda:0` mapping to physical GPU4.
- Result: `LATENT_MONITOR_PASS_VJEPA2_SMOKE` / `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS` on 4/4 asset-complete calibration pairs.
- Positive V-JEPA embedding margin rows: 4/4.
- Positive token-relation margin rows: 4/4.
- This supports a v15 monitor/regularizer direction for catching artifact amplification, but it is still monitor-only and not an auxiliary-loss training integration.
- DPO recipe decision remains `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400/large DPO remain blocked because previous DPO checkpoint videos degraded.


## v14 V-JEPA2 Latent Monitor Test Update (2026-07-07T22:33:45Z)

- `python3 -m compileall cam_physgeo/dpo/latent_relation_monitor_v14.py tests/test_latent_relation_monitor_v14.py`: PASS.
- Direct smoke for latent monitor tests: PASS.
- V-JEPA2 video/token relation smoke: `LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS`, 4/4 ok rows.
- `pytest` remains unavailable in the active H20 shell; no pytest PASS is claimed.


## v14 Broad V-JEPA2 Latent Monitor Coverage Update (2026-07-07T23:06:28Z)

- Coverage summary: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`.
- Combined monitor CSV: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`.
- Coverage table: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_coverage_summary.csv`.
- Ran bounded V-JEPA2 monitor on calibration4, synthetic10, stratified100, S_pass4, and rollout15 subsets.
- Combined rows: 133; ok rows: 74; asset/path error rows: 59.
- For every row where both WIN and LOSE videos were available, V-JEPA2 distinguished the loser: positive V-JEPA margin 74/74 and positive token-relation margin 74/74.
- Stratified100: 64/100 ok, 64/64 positive token-relation margins. The 36 failures are missing old rollout/v10 local_assets videos.
- S_pass4 and rollout15 currently have 0 ok rows because their loser rollout video assets are missing from local_assets; this is recorded as an asset coverage blocker, not a latent-backend failure.
- Decision: `LATENT_MONITOR_PASS_VJEPA2_SMOKE_WITH_ASSET_BLOCKERS`.
- DPO recipe decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO scale is allowed until checkpoint video quality passes.


## v14 Broad V-JEPA2 Coverage Test Update (2026-07-07T23:07:07Z)

- `python3 -m compileall cam_physgeo/dpo/latent_relation_monitor_v14.py tests/test_latent_relation_monitor_v14.py`: PASS.
- Direct smoke for path/index helpers: PASS.
- Broad V-JEPA2 monitor: calibration4/synthetic10/stratified100/S_pass4/rollout15 completed with explicit ok/error rows.
- Combined result: 133 rows, 74 ok, 74/74 positive token-relation margins among available videos.
- `pytest` is still unavailable in the active shell, so no pytest PASS is claimed.


## v14 Missing Rollout Asset Search Update (2026-07-07T23:09:58Z)

- Search report: `reports/dpo_utility_calibration_v14/latent_monitor/missing_rollout_asset_search.md`.
- Bounded search over `/home/nvme03` and `/home/nvme04` did not find representative missing S_pass/rollout loser MP4 files.
- This confirms the S_pass4 and rollout15 V-JEPA2 failures are asset-coverage blockers, not latent-backend failures.
- Available synthetic/v11 rows remain `LATENT_MONITOR_PASS_VJEPA2_SMOKE_WITH_ASSET_BLOCKERS` with 74/74 positive token-relation margins among ok rows.


## v14 Final Requirement Audit Update (2026-07-07T23:12:51Z)

- Current authoritative audit: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14` / `NO_SCALE`.
- V-JEPA2 monitor status is now `PASS_WITH_ASSET_BLOCKERS`, not backend-only blocked: 74/74 available rows have positive token-relation margins.
- Remaining blockers are true-video degradation for scalar-positive DPO schemes, missing old rollout loser assets, and all500 real-energy runtime/cache cost.
- No S16/S32/train400/large DPO is allowed from v14.
