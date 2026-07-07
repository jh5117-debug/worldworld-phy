# DPO Utility Calibration And Latent Monitor v14 Report

## Inputs

- Canonical ready500: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- v14 subsets: `manifests/dpo_v14_subsets/`
- v13b real training CSVs: listed in `reports/dpo_utility_calibration_v14/beta_loss_response_inputs.txt`

## Pair Inventory

See `reports/dpo_utility_calibration_v14/pair_inventory_summary.md`.

- all500: 500 reviewed rows
- rollout/other: 15
- synthetic controlled: 485
- local/time mask available: 485
- stratified100: 100
- S_pass: 4
- S_fail: 0

## Real Energy Calibration

Attempted `full_real_energy_audit run-shard` on `S_pass` with `CUDA_VISIBLE_DEVICES=4`, `--limit 1`, and a 300 second timeout.

Result: timeout before first pair row. Output path:
`reports/dpo_utility_calibration_v14/real_energy_s_pass_smoke/stdout.log`.

Because no real row was written, v14 all500/subset utility CSVs are marked `MISSING_REAL_ENERGY` and must not be used as real energy evidence.

## Beta / Loss Response

See:
- `reports/dpo_utility_calibration_v14/beta_loss_response.csv`
- `reports/dpo_utility_calibration_v14/beta_loss_response_summary.md`
- `reports/dpo_utility_calibration_v14/recommended_dpo_scale.json`
- `reports/dpo_utility_calibration_v14/gap_scale_root_cause.md`

Main result:
- beta=0.1 gives median |beta*u_log| around `2.05e-05` and near-zero ratio 1.0.
- beta=1000 gives median |beta*u_log| around `0.2046` and effective ratio around `0.889`.

Interpretation: v13b DPO preference branch was under-scaled. The observed no-signal behavior is mathematically expected at beta=0.1.

## Latent Monitor

See `reports/dpo_utility_calibration_v14/latent_monitor/backend_audit.md`.

Decision: `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING`.

The audit found local candidates such as VideoMAE code, I3D TorchScript, CLIP import, and WMReward/vjepa2 demo files, but no TRD/VJEPA monitor scores were produced. This is not a latent monitor PASS.

## Normalization Design

See `reports/dpo_utility_calibration_v14/normalization_regularization_design.md` and `configs/cam_physgeo/dpo_objective_v14_normalized.yaml`.

Recommended first calibrated objective family:
- `u_log`
- beta around 1000
- loser detached
- explicit winner anchor
- L0 camera r4 scope
- max 200 steps
- mandatory checkpoint video + metrics + Codex audit

## Should DPO Continue?

Tiny calibrated DPO can be considered next, but only as a guarded probe. Train400, S32/S64, and large DPO remain blocked.

## Safety Confirmation

- No large DPO run.
- No train400 run.
- No StageA/StageB/GRPO/broad-LoRA run.
- No checkpoint/data/weight deletion.
- No videos/images/checkpoints pushed.
- GPU4 was used only for the bounded real-energy smoke; GPU0/1/2/3/6/7 were not used by v14 commands.

## v14 Objective Runner Scaffold

`cam_physgeo.dpo.dpo_objective_search_v14` now supports a dry-run E02 calibrated winner-detached-log scheme using the recommended beta from `recommended_dpo_scale.json`. Training was not launched yet because runtime early-stop plus checkpoint video/metrics gate still needs to be connected before a 200-step job is safe.

## E02 Smoke10 Training Signal

A bounded 10-step `E02_smoke10` run was launched on physical GPU4 only with `CUDA_VISIBLE_DEVICES=4`.

- Objective: `calibrated_winner_detached_log`
- Beta: `1000`
- Scope: `L0_camera_r4`
- Rows: `10`
- Mean winner_improvement_post: `8.374452590942383e-05`
- Final winner_improvement_post: `-4.172325134277344e-05`
- Mean WCR: `0.6669103726560174`
- Decision: `TRAINING_SIGNAL_FAIL_WINNER`

This confirms beta calibration fixes the 0.693 no-signal issue, but E02 still fails because the final winner improvement flips negative. No checkpoint video/metrics gate was run for this failed training signal. Next safe probe is lower LR / best-step early-stop, not scale.

## E03 Smoke10 Early Stop

`E03_smoke10` was launched on physical GPU5 only with lower LR/lambda_pref. It produced `2` rows and hit `WINNER_WORSE` by step 1, so the own E03 process was stopped early according to the gate policy. Decision: `TRAINING_SIGNAL_FAIL_WINNER`. Lower LR alone did not solve winner instability.


## E02 Best7 Training Signal

`E02_best7` reran the calibrated winner-detached-log scheme for 7 steps, matching the best-step region found by E02_smoke10.

- Rows: `7` / `7`
- Mean winner_improvement_post: `0.00010894877570016044`
- Final winner_improvement_post: `0.00033855438232421875`
- Mean WCR: `0.6667287038434788`
- Mean loser_degradation_post: `-2.8984887259347098e-05`
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_V14`

This is the first v14 training-signal pass, but it is not a final recipe. The next required gate is checkpoint video generation, PSNR/SSIM/LPIPS/FVD/VBench/PhysGeo metrics, and Codex visual audit for step0/step5/step7. No scaling is allowed before that gate passes.


## E02_best7 Checkpoint Video Audit Update (2026-07-07T02:37:56.080956Z)

- Candidate: `E02_best7` / `calibrated_winner_detached_log` / `beta=1000` / `L0_camera_r4`.
- Training signal: `TRAINING_SIGNAL_PASS`.
- Mean winner improvement post: `0.00010894877570016044`.
- Final winner improvement post: `0.00033855438232421875`.
- Mean winner contribution ratio: `0.6680136300480072`.
- True V2V-5 checkpoint videos generated: `12` (`step000`, `step005`, `step007` on 4 validation samples).
- Codex visual audit: `FAIL`. Final `step007` is worse than `step000` on multiple samples due to duplicate objects, hallucinated blobs/fragments, and foreground object-count/identity drift.
- Metrics: PSNR/SSIM rows `12/12`; LPIPS GPU smoke `PASS`; FVD remains `BLOCKED_BY_ENV`; VBench real checkpoint scoring not configured in this wrapper.
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_VIDEO_FAIL_V14`.
- Scale permission: `NO_SCALE`; do not run S16/S32/train400 from this recipe.

Relevant paths:
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit.csv`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit_summary.md`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/metrics/metrics_summary.md`

## v14 Objective Search Update (2026-07-07T03:56:37.931118Z)

- Added E04_screen5 and E05_screen5 screening runs on physical GPU4/GPU5 only.
- E04_screen5 (`no_lose_gap_normalized_win_only`) training signal PASS: mean winner improvement `0.00012879371643066407`, final `0.00013786554336547852`, WCR `0.7916`, loser degradation negative.
- E05_screen5 (`normalized_clipped_loser`, alpha_l=0.02) training signal PASS: mean winner improvement `0.00012555122375488282`, final `0.00012230873107910156`, WCR `0.8220`, slight loser degradation.
- E04 checkpoint videos generated: `8` true V2V-5 videos. Codex visual audit FAIL: step005 worsens object count/identity in multiple samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400.

## E05 Screen5 Checkpoint Audit Update (2026-07-07T05:04:09.871964Z)

E05 tested `normalized_clipped_loser` with `L0_camera_r4` for 5 steps. Training signal was healthy: mean winner improvement post was `0.00012555122375488282`, final winner improvement post was `0.00012230873107910156`, and mean winner contribution ratio was `0.8245008192953873`.

Checkpoint evaluation generated true V2V-5 videos for step000 and step005 on the 4-sample validation set. PSNR/SSIM/LPIPS ran successfully for `8/8` rows. FVD remains blocked in the current wrapper by missing real video-FVD backend dependencies/weights; VBench imports but real project-local scoring remains unconfigured in this wrapper.

Codex visual audit failed the gate: `2/4` samples were worse at step005. The dominant visible failures were new foreground fragments, object duplication, floating object artifacts, and object-count drift. Therefore E05 is only a training-signal candidate, not a valid DPO recipe.

Current final decision remains `DPO_RECIPE_NOT_FOUND_V14`; train400 and large DPO remain blocked.

## E01/E06 20-Step Screen Update (2026-07-07T06:06:00.444732Z)

Two additional v14 schemes were run under the GPU4/5 constraint. `E01_screen20` used calibrated raw winner-detached utility and passed training signal over 20 steps: mean winner improvement post `0.00014046728610992432`, final winner improvement post `0.0002976655960083008`, and mean WCR `0.9046868415246985`. `E06_screen20` used normalized clipped loser with alpha=0.05 and also passed training signal: mean winner improvement post `0.0001410573720932007`, final winner improvement post `0.00028055906295776367`, and mean WCR `0.8179387603935927`.

However, E06 checkpoint video evaluation did not pass. A parallel step000/step020 eval and then a single step020 retry stalled at `instantiate WanI2VFast`; GPU memory stayed essentially unallocated and no MP4 videos were produced. Therefore E06 is only a training-signal candidate, not a valid DPO recipe. E01 has not passed video/metric/Codex audit either.

Current decision remains `DPO_RECIPE_NOT_FOUND_V14`; no scale is allowed.

## E07-E10 Objective Search Update (2026-07-08 CST)

Decision: `DPO_RECIPE_NOT_FOUND_V14`.

The later v14 schemes show that beta/utility calibration fixed the pure no-signal issue at the scalar training level, but it did not produce a valid DPO recipe because true V2V-5 checkpoint videos still degrade.

Summary:

- `E07_screen200` (`linear_winner_detached`, L0 camera r4) completed 200 steps with strong training signal: final winner improvement `+0.0161217451`, mean WCR `0.984991`, mean loser degradation negative. True V2V-5 step200 videos were worse than step0 on 4/4 fixed val samples. Decision: `VISUAL_GATE_FAIL_STEP200_WORSE`.
- `E08_screen200` (`calibrated_winner_detached_log`, L0 camera r4) completed 200 steps with strong training signal: final winner improvement `+0.0144469738`, mean WCR `0.979487`, mean loser degradation negative. It remains training-signal-only because video/metrics audit was not run.
- `E09_screen200` (`source_weighted_rollout_priority`, L0 camera r4) was stopped after a strong step50 early-best checkpoint: winner improvement `+0.0014111996`, WCR `1.0`, loser degradation negative. True V2V-5 step50 videos were worse or not better on 4/4 samples. Decision: `VISUAL_GATE_FAIL_STEP050_WORSE`.
- `E10_screen100` (`calibrated_winner_detached_log`, L2 camera-temporal r4) completed 100 steps with training signal: final winner improvement `+0.0004041791`, mean winner improvement `+0.0001850957`, WCR `0.824683`, mean loser degradation negative. True V2V-5 step100 videos were worse on 2/4 samples and not decisively better on the rest. Decision: `VISUAL_GATE_FAIL_STEP100_WORSE`.

Current blocker: energy/gap improvements do not guarantee visual quality. The active failure mode is rollout artifact amplification: foreground duplication, object identity clutter, green/blob fragments, white/yellow line or text-like artifacts, and scene contamination.

Scale decision:

- Do not run S16/S32 continuation from these schemes.
- Do not run train400.
- Do not run large DPO.
- Next safe direction is to add a rollout-quality/latent monitor or regularizer that detects these artifacts before or during DPO updates.


## v14 Final Test Status

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Targeted pytest suite: NOT RUN because `pytest` is unavailable in the active H20 shell. No pytest PASS is claimed.
- Test status path: `reports/dpo_utility_calibration_v14/test_status.md`.

## v14 Requirement Audit (2026-07-07T18:10:35Z)

- Requirement audit path: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14`.
- All500 energy CSVs are coverage/blocker files with `MISSING_REAL_ENERGY`, not real energy calibration evidence.
- Latent monitor is `LATENT_MONITOR_BLOCKED` because no TRD/VJEPA margins were produced.
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

## Real-Energy Blocker Retry After Adapter Repair

A follow-up retry built `manifests/dpo_v14_subsets/asset_complete_prefix5_onepair_for_energy.jsonl` from an asset-complete synthetic controlled pair. Temporary reconstructed videos were written only under `local_assets/dpo_utility_calibration_v14/blocker_retry/` and are not for git.

The adapted manifest passed `prefix5_schema_errors`. Running `full_real_energy_audit` with the active conda Python failed because user-site Transformers/HuggingFace Hub versions are incompatible. Re-running with `/usr/bin/python3` fixed imports and loaded all 16 LingBot shards, then entered the VAE path, but hit the 900 second timeout before the first energy row.

Current blocker: `REAL_ENERGY_CALIBRATION_BLOCKED_FORWARD_TIMEOUT`. This does not change the DPO decision: no v14 recipe passed both scalar and true-video gates.

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


## DINOv2 Frame Latent Monitor Smoke (2026-07-07T22:19:25Z)

A local DINOv2 ViT-S/14 frame fallback monitor was implemented in `cam_physgeo/dpo/latent_relation_monitor_v14.py` and run on the 4 asset-complete calibration pairs.

Evidence:

- `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke.csv`
- `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke_summary.md`
- `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke_summary.json`

Result: `LATENT_MONITOR_DINO_FRAME_SMOKE_PASS`. All 4 rows completed with finite positive frame cosine margins and finite positive temporal-relation margins. This provides a bounded monitor signal that can distinguish the controlled WIN/LOSE pairs better than the scalar energy-only gate in this small smoke.

Limitations: this is not full V-JEPA/VideoREPA/TRD training integration. The clean winner is used as the local reference for synthetic controlled pairs, so the winner-reference distance is trivially zero and the useful quantities are loser-to-winner frame distance and loser/winner temporal-relation distance. It should be used as a v15 monitor candidate, not as permission to scale v14 DPO.

Decision remains `DPO_RECIPE_NOT_FOUND_V14`: scalar DPO schemes can improve energy/gap metrics, but validated checkpoint videos still degrade. No S16/S32/train400/large DPO is allowed from this evidence alone.


## V-JEPA2 Token-Relation Monitor Smoke (2026-07-07T22:32:50Z)

A real local V-JEPA2.1 ViT-B EMA encoder monitor was run on the 4 asset-complete calibration pairs using 8 sparse future frames at 224px. The model was built from the local torch hub checkout and loaded strict from `/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt` with 0 missing and 0 unexpected keys. No download and no training occurred.

Evidence:

- `reports/dpo_utility_calibration_v14/latent_monitor/vjepa2_video_smoke.csv`
- `reports/dpo_utility_calibration_v14/latent_monitor/vjepa2_video_smoke_summary.md`
- `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`
- `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`

Result: `LATENT_MONITOR_PASS_VJEPA2_SMOKE`. All 4 rows completed and all 4 had positive V-JEPA embedding margins plus positive token-relation margins. Per-pair token-relation margins were approximately `0.0388`, `0.0382`, `0.0408`, and `0.0422`.

Interpretation: the requested latent monitor direction is viable as a monitor on this small controlled set. It does not rescue v14 DPO because E07/E09/E10 still failed true checkpoint video gates; instead it gives the next safe v15 action: add V-JEPA2/DINO rollout-quality monitoring or regularization before any further DPO scale.


## Broad V-JEPA2 Coverage Result (2026-07-07T23:06:28Z)

The V-JEPA2 monitor was expanded beyond the 4-pair calibration smoke. It now covers multiple v14 subsets with explicit error accounting:

- calibration4: 4/4 ok, 4/4 positive relation margins.
- synthetic10: 6/10 ok, 6/6 positive relation margins; the 4 failures are old v10 loser asset misses.
- stratified100: 64/100 ok, 64/64 positive relation margins; failures are old rollout/v10 local_assets misses.
- S_pass4: 0/4 ok because loser video assets are missing.
- rollout15: 0/15 ok because rollout loser video assets are missing.

Required latent monitor artifacts are now populated:

- `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`
- `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`
- `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_coverage_summary.csv`

Conclusion: V-JEPA2 is viable as a v15 monitor/regularizer candidate for available videos. The remaining limitation is asset coverage for old rollout/v10 pairs, plus the unchanged v14 DPO failure that scalar-improved checkpoints degrade real V2V-5 video.
