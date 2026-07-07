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
