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
