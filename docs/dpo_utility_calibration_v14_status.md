# DPO Utility Calibration v14 Status

Updated: 2026-07-07 CST

## Current State

- Canonical repaired ready500 remains the required data entry.
- v13b completed with `DPO_RECIPE_NOT_FOUND`.
- v14 PRD was committed in `57ba7dd`.
- Pair inventory completed: all500=500, rollout/other=15, synthetic_controlled=485, local_mask=485, stratified100=100, S_pass=4, S_fail=0.
- One-pair real LingBot energy smoke on GPU4 timed out after 300 seconds before writing a row.
- Therefore `energy_utility_*.csv` files currently mark `MISSING_REAL_ENERGY`; they are coverage/blocker files, not real all500 energy calibration.
- Beta/loss response was computed from v13b real training CSVs.
- Recommended utility from v13b evidence: `u_log`.
- Recommended beta from v13b evidence: `1000` with median |beta*u| `0.20455321269580987`.
- Latent monitor audit found backend candidates but did not produce TRD/VJEPA scores; decision `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING`.

## Current Blockers

1. Real all500 LingBot energy calibration is blocked by runtime/model initialization timeout.
2. V-JEPA/VideoREPA/TRD monitor is not validated; no latent scores have been produced.
3. A calibrated DPO scheme is designed but not yet run in this v14 phase.

## Decision

Do not run train400 or large DPO. The next safe training probe, after the user accepts the blocker/scale diagnosis, is a tiny guarded `calibrated_winner_detached_log` run on S_pass/S8 with beta around 1000, loser detached, explicit winner anchor, checkpoint video, metrics, and Codex audit.

## E02 Smoke10 Update

- `E02_smoke10` ran 10/10 steps on physical GPU4 only.
- Mean winner improvement was positive, and DPO loss moved away from 0.693.
- Final winner improvement flipped negative: `-4.172325134277344e-05`.
- Decision: `TRAINING_SIGNAL_FAIL_WINNER`.
- Do not scale; next probe should test lower LR / best-step early stop.

## E03 Smoke10 Update

- `E03_smoke10` used physical GPU5 only.
- It was stopped early after `2` rows because winner improvement became negative.
- Decision: `TRAINING_SIGNAL_FAIL_WINNER`.
- Next safe direction: E02 best-step early stop / stronger winner protection, not scale.


## E02 Best7 Training-Signal Update

- `E02_best7` ran on physical GPU4 only with `CUDA_VISIBLE_DEVICES=4`.
- Objective: `calibrated_winner_detached_log`, utility `u_log`, beta `1000`, L0 camera r4.
- Steps: `7/7`.
- Mean winner_improvement_post: `0.00010894877570016044`.
- Final winner_improvement_post: `0.00033855438232421875`.
- Mean winner_contribution_ratio_post: `0.6667287038434788`.
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_V14` / `TRAINING_SIGNAL_PASS`.
- Checkpoint video, metrics, and Codex visual audit are still pending; train400 and large DPO remain blocked.
