# EXP_004 Anchored DPO Probe

Updated: 2026-06-24 12:47:51 CST  
Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`  
Branch: `research/quant-small-lora-dpo-probe-20260624`  
Start commit: `63d1b93`  

This PRD is written before experiment launch. It must be updated after results are parsed and before the next stage is considered complete.


## Problem and Hypothesis

Current rollout quality is too poor for self-rollout DPO. Anchored DPO should start from clean GT winners and quality-bounded hard-negative losers.

## Unique Variable

DPO objective on curated anchored pairs only. No large-scale DPO and no GRPO.

## Candidate Sources

- clean GT as winner
- controlled corrupted GT as loser
- Original LingBot-Fast rollouts
- last-week camera-only tiny LoRA rollouts
- best small-LoRA sweep model if one passes
- broad-LoRA failed model only as negative candidate after quality-floor filtering

## Pair Policy

A. GT winner vs controlled corrupted GT loser.  
B. GT winner vs quality-qualified bad rollout loser.  
C. high-quality rollout winner vs worse rollout loser only if winner absolute quality passes.

Do not use trivial horrible losers. Loser must pass quality floor and be a hard negative in a small number of dimensions.

## Quality Floor

No black/corrupt video, no severe blur, no global freeze, foreground main object exists, no total scene replacement, R_quality above candidate 25th percentile, freeze penalty below threshold.

## DPO BF16 Preflight

GPU7 2 steps, GPU6/7 DDP 5 steps, GPU0-7 DDP 5 steps. Check no SIGFPE/OOM/NaN, reference frozen, same noise/timestep, finite DPO loss, gradients nonzero, save/load, stable memory.

## Probe

20-50 pairs, max 50-100 optimizer steps, low-rank small LoRA, frozen Original Fast reference. Monitor DPO loss, implicit accuracy, policy/reference winner/loser energy gaps, KL/reference drift proxy, gradients, memory, step time.

## Success Gate

Learning signal is non-saturated, winner-relative score improves, at least one quantitative metric improves, FG-ID/Quality do not degrade, and before/after video audit does not show collapse.

## Outputs

- `manifests/anchored_dpo_probe_pairs.jsonl`
- `reports/anchored_dpo_probe_pair_report.md`
- `docs/anchored_dpo_probe_report.md`

## Stop Conditions

Stop on saturated implicit accuracy with near-zero DPO loss, winner degradation, loser-only degradation, NaN/OOM/SIGFPE, or widespread visual collapse.

## Git Commit

Post-probe commit: `Validate BF16 DPO and document probe results`.

## Status

PLANNED_PRELAUNCH.
