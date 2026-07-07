# v14 Blocker Resolution Plan

Current decision: `DPO_RECIPE_NOT_FOUND_V14`.

This plan does not authorize scale. It turns the remaining v14 blockers into bounded, explicit next actions.

## Blocker 1: all500 real LingBot energy calibration

Status: `BLOCKED_REAL_ENERGY_RUNTIME_TIMEOUT`.

Evidence: `energy_utility_*.csv` rows are coverage rows with `MISSING_REAL_ENERGY`; one S_pass real-energy smoke timed out after 300 seconds before writing a pair row.

Next bounded action:

1. Run only a one-pair S_pass real-energy retry on physical GPU4 or GPU5.
2. Require incremental CSV/JSONL output before any all500 attempt.
3. Use `timeout 900s`; if no row appears, stop and keep all500 blocked.
4. Do not train; do not launch DPO.

Dry-run command generator:

```bash
bash scripts/plan_v14_blocker_retry.sh
```

Actual execution, only when explicitly authorized:

```bash
RUN_V14_BLOCKER_RETRY=1 V14_RETRY_GPU=4 bash scripts/plan_v14_blocker_retry.sh
```

## Blocker 2: latent V-JEPA / VideoREPA / TRD monitor

Status: `LATENT_MONITOR_BLOCKED`.

Evidence: local imports/files were found, but no valid TRD/VJEPA winner-vs-loser margins were produced. No latent auxiliary loss is enabled.

Next bounded action:

1. Inspect local WMReward/VJEPA2 scripts and available weights without downloading models.
2. If a local checkpoint is found, run S_pass only and require finite winner/loser distances.
3. PASS requires WIN/LOSE discrimination; otherwise keep monitor blocked.
4. Do not integrate into training until monitor PASS.

## Blocker 3: scalar gap improves but videos worsen

Status: `VISUAL_GATE_FAIL_AFTER_SCALAR_SIGNAL`.

Evidence: E09 and E10 had healthy scalar training signals, but true V2V-5 rollouts worsened with duplication, fragments, and scene contamination.

Next bounded action:

1. Add rollout-quality monitor/regularizer before any new DPO scale.
2. Treat artifact increase as a hard stop even when winner energy improves.
3. Use E09/E10 as negative examples for monitor calibration.

## Permissions

- Allowed GPUs: physical GPU4/GPU5 only.
- Forbidden: GPU0/1/2/3/6/7.
- No train400, no large DPO, no StageA/StageB/GRPO, no broad-LoRA.
- No checkpoint/data/weight deletion.
- No videos/images/checkpoints/weights pushed.

## Retry script correction

The retry script now calls `cam_physgeo.dpo.full_real_energy_audit run-shard --limit 1`, which is the real LingBot-Fast energy audit path. It no longer calls the planning-only `utility_calibration_v14.py` CLI for real energy.
