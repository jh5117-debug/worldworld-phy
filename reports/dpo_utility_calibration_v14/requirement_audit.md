# v14 Requirement Audit

Updated: `2026-07-07T23:12:51Z`

This is the current authoritative audit for `EXP_dpo_utility_calibration_and_latent_monitor_v14`. It preserves the original scope: offline utility calibration, latent monitor validation, calibrated <=200-step DPO objective search, checkpoint video/metric gates, and a no-scale decision unless every gate passes.

## Final Decision

- Final DPO decision: `DPO_RECIPE_NOT_FOUND_V14`
- Scale permission: `NO_SCALE`
- S16/S32 permission: `NO`
- train400 permission: `NO`
- Large DPO permission: `NO`
- Next safe direction: v15 rollout-quality / V-JEPA2-DINO latent monitor or regularizer before any additional DPO scaling.

## Requirement Status Table

| Requirement | Status | Evidence |
|---|---|---|
| H20 repo / branch / GPU4-5 scope | `PASS` | Runs were executed on H20 branch `research/quant-small-lora-dpo-probe-20260624`; monitor/training commands used `CUDA_VISIBLE_DEVICES=4` or `5`; no v14 training scale was launched on forbidden GPUs. |
| PRD before experiment | `PASS` | `docs/experiments/EXP_dpo_utility_calibration_and_latent_monitor_v14.md`. |
| Pair inventory / subsets | `PASS` | `reports/dpo_utility_calibration_v14/pair_inventory_summary.md`; `manifests/dpo_v14_subsets/all500.jsonl`, `s_pass.jsonl`, `s_fail.jsonl`, `rollout_only.jsonl`, `synthetic_controlled.jsonl`, `stratified100.jsonl`, `local_mask.jsonl`. |
| all500/S_pass/rollout real LingBot energy calibration | `BLOCKED_PARTIAL` | `energy_utility_*.csv` coverage files exist but are `MISSING_REAL_ENERGY`; asset-complete calibration12 produced 12/12 real energy rows with CUDA runtime, but all500 remains too expensive without batching/cache and old rollout assets are missing. |
| Utility / beta response | `PASS_WITH_LIMITS` | `reports/dpo_utility_calibration_v14/recommended_dpo_scale.json` recommends `u_log` and beta `1000`; `gap_scale_root_cause.md` documents why beta=0.1 was no-signal. Limit: based primarily on v13b training CSVs and calibration12, not full all500 real energy. |
| Normalization / regularization design | `PASS` | `reports/dpo_utility_calibration_v14/normalization_regularization_design.md`; `configs/cam_physgeo/dpo_objective_v14_normalized.yaml`. |
| DINO latent monitor | `PASS_SMOKE` | `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke_summary.md`: 4/4 calibration rows positive frame and temporal relation margins. |
| V-JEPA / TRD-style latent monitor | `PASS_WITH_ASSET_BLOCKERS` | `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_summary.md`: combined 133 rows, 74 ok, 74/74 positive token-relation margins among available videos. `S_pass4`/`rollout15` blocked by missing old loser videos, not model failure. |
| 10 calibrated schemes | `COMPLETE_NO_RECIPE` | `reports/dpo_utility_calibration_v14/search_summary.md`; `best_scheme_decision.json`; E01-E10 attempted/screens run. E07/E08/E09/E10 scalar signals improve but no scheme passes video/metric gates. |
| Checkpoint video / visual gates | `FAIL_FOR_PROMISING_SCHEMES` | E07 step200 worse 4/4; E09 step50 worse/not-better 4/4; E10 step100 worse 2/4 and not clearly better on remaining samples. |
| Metrics gates | `PARTIAL` | PSNR/SSIM/LPIPS available for several checkpoint evals; FVD/VBench wrapper coverage remains incomplete in v14. Visual gate failures already block scale. |
| Exact blocker if no recipe | `PASS` | Active blocker: scalar energy/gap improvements do not predict true V2V-5 visual quality; updates amplify foreground duplication, fragments, identity clutter, line/text artifacts, and scene contamination. Secondary blockers: all500 real energy cost/cache and missing old rollout loser assets. |
| Tests | `PARTIAL_PASS` | `python3 -m compileall cam_physgeo src tests` PASS previously; targeted direct smoke for latent monitor helper tests PASS. `pytest` unavailable in active H20 shell, no pytest PASS claimed. |
| Git artifact policy | `PASS` | Pushed source/tests/docs and small CSV/JSON/MD only; no local_assets, videos, images, checkpoints, weights, or large logs. |

## Energy Calibration Evidence

- Asset-complete calibration12 real-energy run: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.csv`.
- Gap-scale summary: `reports/dpo_utility_calibration_v14/real_energy_gap_scale_calibration4_summary.md`.
- Finding: at policy=reference init, DPO utility is exactly zero; training utilities around `1e-4` need beta around `1000`, not `0.1`.

## Latent Monitor Evidence

- DINO: `reports/dpo_utility_calibration_v14/latent_monitor/dinov2_frame_smoke.csv`.
- V-JEPA combined: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_monitor.csv`.
- V-JEPA coverage: `reports/dpo_utility_calibration_v14/latent_monitor/trd_vjepa_coverage_summary.csv`.
- Missing rollout asset search: `reports/dpo_utility_calibration_v14/latent_monitor/missing_rollout_asset_search.md`.

## Objective Search Evidence

- Search summary: `reports/dpo_utility_calibration_v14/search_summary.md`.
- Best-scheme decision: `reports/dpo_utility_calibration_v14/best_scheme_decision.json`.
- E07/E09/E10 checkpoint audits document the visual failures that block scale.

## Current Answer To v14 Questions

1. `u ~ 1e-4` because full-future reduced energy gaps are tiny relative to the old beta; beta=0.1 creates near-zero logits.
2. `u_log` with beta around `1000` remains the best nonzero training-utility scale from prior training CSVs; fresh policy=reference calibration12 has exactly zero utility and therefore recommends `NONE_ZERO_UTILITY`. Full all500 real-energy confirmation is still blocked.
3. Normalization helps scalar training but does not prevent visual artifact amplification.
4. V-JEPA2/DINO latent monitor can distinguish available WIN/LOSE videos and is a viable v15 monitor/regularizer candidate.
5. No DPO scheme can proceed to S16/S32/train400 because true checkpoint videos degrade.
