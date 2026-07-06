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
