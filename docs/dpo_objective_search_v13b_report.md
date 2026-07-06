# DPO Objective Search v13b Report

Updated: 2026-07-06T13:08:17+08:00

## Goal

Search 6-10 tiny DPO objective / LoRA / gap-normalization variants on GPU4 and GPU5 only, looking for at least one recipe that stays healthy within 200 steps before any scale-up.

## Data

Canonical data entry:

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`

v13b subsets generated:

- `manifests/dpo_v13b_subsets/s4_pass.jsonl`
- `manifests/dpo_v13b_subsets/s8_pass_expand.jsonl`
- `manifests/dpo_v13b_subsets/s16_confident.jsonl`
- `manifests/dpo_v13b_subsets/s4_local_mask.jsonl`
- `manifests/dpo_v13b_subsets/val_video_4.jsonl`

Summary:

- `reports/dpo_objective_search_v13b/subset_summary.csv`
- `reports/dpo_objective_search_v13b/subset_summary.md`

## Code Prepared

The v13b implementation adds:

- unified gap metrics: `win_gap`, `lose_gap`, `g_w`, `g_l`, clipped loser gap, winner contribution ratio, loser dominance, health flags;
- small objective scheme runner for S01-S10;
- GPU4/5-only scheduler and gate checks;
- conservative scheduler behavior that blocks when GPU status cannot be queried or GPU4/5 are not idle;
- direct dry-run support that does not touch GPUs.

## Candidate Schemes

Prepared schemes:

- S01 `winner_detached_pref_low`
- S02 `winner_detached_pref_lower_lr`
- S03 `winner_detached_pref_earlystop_best`
- S04 `no_lose_gap_normalized_win_only`
- S05 `normalized_clipped_loser_alpha005`
- S06 `normalized_clipped_loser_alpha010`
- S07 `linear_winner_detached`
- S08 `delayed_loser_gradient_tiny`
- S09 `local_time_mask_winner_detached`
- S10 `lora_camera_temporal_winner_detached`

No scheme was trained because GPU4/5 were occupied.

## Validation

Completed:

- `python3 -m compileall cam_physgeo src tests`: PASS.
- subset builder direct smoke: PASS.
- S01 dry-run: PASS.
- scheduler dry-run: PASS with decision `GPU4_5_BLOCKED`.
- gap/gate direct smoke: PASS.

`pytest` is not installed in the system Python, so no pytest result is claimed.

## GPU Finding

Independent pmon showed physical GPU4 and GPU5 occupied by existing non-v13b `python` jobs. The scheduler therefore did not launch any training. This complies with the user rule not to kill unknown tasks and not to use forbidden GPUs.

## Decision

`DPO_RECIPE_GPU_BLOCKED`

No DPO recipe can be judged yet because no v13b training job was allowed to run. The next action is to relaunch the scheduler when physical GPU4 or GPU5 is idle:

```bash
bash scripts/launch_dpo_objective_search_v13b.sh
```

The scheduler must still be monitored to verify any launched job uses only `CUDA_VISIBLE_DEVICES=4` or `CUDA_VISIBLE_DEVICES=5`.

## Explicit Non-Runs

- No large DPO.
- No train400.
- No StageA.
- No StageB.
- No GRPO.
- No broad-LoRA.
- No checkpoint deletion.
- No data/weights/video pushed.

## Interim Result - 2026-07-06T16:47:05

- GPU policy: v13b training/eval used only physical GPU4/5; forbidden GPU0/1/2/3/6/7 were not used by v13b.
- Schemes attempted so far: S01 and S02.
- S01 is the current best training-signal candidate, but it is not accepted as a DPO recipe until video/metrics/audit pass.
- Safe eval loader repairs completed:
  - force local safetensors and low CPU memory loading;
  - no-op `WanModelFast.init_weights` during `from_pretrained`;
  - support nested DPO pair manifest fields for checkpoint eval.
- Current blocker is GPU4/5 occupancy by older rollout/eval jobs. The v13b waiter is non-destructive and does not kill those jobs.
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY`; train400 and large DPO remain blocked.
## Final v13b Decision - 2026-07-07

Decision: DPO_RECIPE_NOT_FOUND. This round did not find a 200-step DPO recipe that passes both training signal and checkpoint video/metric gates. S07 is the best training-signal candidate, but failed VBench temporal_flickering. S03/S06/S09 confirm the recurring pattern: winner-anchor movement exists, loser degradation is not dominant, but the preference branch is effectively no-signal with dpo_loss near 0.693. S10 did not establish the broader camera+temporal LoRA hypothesis because it blocked before first row. Next step should be offline preference utility/gap-scale calibration before any further training scale.
## S10 Correction - 2026-07-07

After reviewing the correct 100-step CSV path, S10 is reclassified: it produced 18 rows, but final winner_improvement_post was negative and DPO loss stayed near 0.693. The broader camera+temporal LoRA scope therefore did not provide a valid DPO recipe in this run.

