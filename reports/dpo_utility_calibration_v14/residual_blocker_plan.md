# v14 Residual Blocker and Next-Evidence Plan

Updated: 2026-07-08T10:22 CST

Decision remains: `DPO_RECIPE_NOT_FOUND_V14`.
Scale permission remains: `NO_SCALE`.

This file records the requirements from the original v14 objective that are not fully proven, even though the current evidence is sufficient to block DPO scaling. It is intentionally not a success rewrite.

## Current Proven Points

- H20 repo/branch and GPU policy were followed for v14 active jobs: GPU4/GPU5 only for energy, latent monitor, and objective search work.
- Canonical repaired ready500 and v14 subset inventory exist.
- Calibration moved beyond one-pair smoke: diverse12 real LingBot energy completed with 12/12 ok rows across 12 synthetic failure types.
- Beta/loss analysis identified why prior `beta=0.1` was effectively no-signal when utility was near `1e-4`.
- Local V-JEPA2 and DINO monitors produced real no-download scores; V-JEPA2 distinguishes available WIN/LOSE pairs and catches checkpoint drift at high recall.
- E07/E09/E10 produced scalar training signal but failed true V2V-5 visual gates.

## Residual Blockers

### 1. All500 / S_pass / rollout real-energy coverage is not complete

Status: `BLOCKED_PARTIAL`.

Evidence:

- `reports/dpo_utility_calibration_v14/energy_utility_all500.csv` has 500 coverage rows, but these are not all real LingBot energy rows.
- `reports/dpo_utility_calibration_v14/energy_utility_s_pass.csv` and `energy_utility_rollout_only.csv` remain limited by missing old rollout loser assets and runtime/cache cost.
- The strongest real-energy evidence is currently `calibration12` plus `diverse12`, not all500 real-energy coverage.

Why this matters:

- The original v14 request asked for ready500 / S_pass / rollout offline calibration. We cannot honestly claim full all500 real-energy calibration.

Next non-training evidence needed:

1. Build a reusable energy cache for asset-complete ready500 rows.
2. Split old rollout rows into `asset_available` and `asset_missing` subsets.
3. Run a bounded `stratified50_real_energy` or `rollout_asset_available_real_energy` job before attempting all500.
4. Estimate real-energy throughput and storage needs before launching any long all500 job.

### 2. Latent monitor is not an approval metric

Status: `PASS_AS_DRIFT_MONITOR`, not full quality gate.

Evidence:

- WIN/LOSE available-video rows show positive V-JEPA2 token-relation margins.
- Expanded checkpoint regression has 24/24 ok rows with positive latent drift margins.
- Gate stats show low AUC against Codex worse/not-worse labels, so V-JEPA2 is high-recall drift/inspection trigger, not standalone approval.

Next non-training evidence needed:

1. Add artifact-specific visual labels to checkpoint eval rows.
2. Calibrate V-JEPA2 thresholds jointly with foreground duplication / identity clutter / line-artifact labels.
3. Treat V-JEPA2 as a v15 monitor or auxiliary candidate only after artifact-specific correlation is measured.

### 3. Objective search produced scalar-positive but visually failing recipes

Status: `COMPLETE_NO_RECIPE` plus `FAIL_FOR_PROMISING_SCHEMES`.

Evidence:

- E07 completed 200 steps with positive scalar signal but step200 videos were worse on 4/4 samples.
- E09 reached strong early signal at step50 but step50 videos were worse on 3/4 and not better on 1/4.
- E10 completed 100 steps with positive scalar signal but step100 videos were worse on 2/4 and not decisively better on the rest.

Exact blocker:

- Current energy/gap objectives reward changes that do not preserve real rollout visual quality. The failure mode is artifact amplification: foreground duplication, object identity clutter, foreground fragments, line/text-like artifacts, and scene contamination.

Next non-training evidence needed:

1. Build artifact-aware checkpoint labels and metrics from the existing E07/E09/E10 rollouts.
2. Define a v15 `artifact_guard` gate before any new DPO recipe search.
3. Only after artifact guard is measurable should a new tiny objective include a V-JEPA2/quality regularizer.

### 4. Metric gates are partial because visual gates already fail

Status: `PARTIAL_BLOCKED_BY_VISUAL_FAIL`.

Evidence:

- Several PSNR/SSIM/LPIPS paths exist.
- VBench/FVD wrappers remain partial for some v14 checkpoint eval directories.
- Since Codex visual audits already fail on promising schemes, missing metric expansion cannot authorize scale.

Next non-training evidence needed:

1. Normalize checkpoint eval output schema across E07/E09/E10.
2. Run metric wrappers only on existing videos, not new training.
3. Record exact VBench/FVD unsupported cases instead of substituting fake metrics.

### 5. Tests are smoke-level, not pytest-complete

Status: `PARTIAL_PASS`.

Evidence:

- `python3 -m compileall cam_physgeo src tests` passed after completion docs.
- Direct import smoke for v14 modules passed.
- `pytest` is unavailable in the active H20 shell, so no pytest pass is claimed.

Next evidence needed:

1. Either install/use a known project test environment with pytest already available, or keep direct smoke tests explicit.
2. Do not claim pytest coverage until it actually runs.

## Safe Next Direction

Do not resume DPO training from v14 recipes.

The next aligned work is v15 monitor/regularizer design:

1. Reuse existing E07/E09/E10 checkpoint videos.
2. Add artifact-specific labels and metrics.
3. Calibrate V-JEPA2/visual-quality monitor as a rejection gate.
4. Design a tiny v15 objective only after the monitor can catch artifact amplification.
5. Keep `NO_SCALE` until true V2V-5 video + metrics + Codex audit pass.

## Explicit Non-Actions

- No large DPO.
- No train400.
- No S32/S64.
- No StageA / StageB / GRPO.
- No broad-LoRA.
- No checkpoint/data/weight deletion.
- No videos/images/checkpoints/weights pushed.

## v14 Artifact Regression Aggregation (2026-07-08T10:25 CST)

- Added aggregation: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_summary.md`.
- Source audits: E07 step200, E09 step50, and E10 step100 true V2V-5 checkpoint visual audits.
- Result: scalar-positive schemes consistently fail visual gates. E07 is worse on 4/4, E09 is flagged worse on 4/4; one row is described as at-best-mixed/not-better, and E10 is worse on 2/4 and not decisively better on the rest.
- Dominant failure tags: identity clutter, foreground duplication/fragments, artifact/line-text contamination, with background/camera contamination in some E09 samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; scale permission remains `NO_SCALE`.
