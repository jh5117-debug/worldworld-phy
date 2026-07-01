# DPO Smoke v7 Report

Current Status: BLOCKED_GPU_BUSY_SUBSET_READY

Updated: 2026-07-01 16:05:00 CST

## Summary

The v7 tiny SDPO-anchor smoke has not started training. The pre-experiment PRD and visual-audit policy were committed and pushed first. A 10-pair GT>C subset was selected from the reviewed v6b DPO-ready pairs and all 10 losers have a v7 loser visual audit record.

## Subset

- Subset manifest: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Subset summary: `reports/dpo_smoke_v7/subset_summary.csv`
- Pair count: 10
- Pair type: GT_C
- Winner: clean GT future
- Loser: C camera+self/temporal-r4 rollout
- Template coverage: 3 drop, 2 collision, 3 roll, 2 containment
- Loser reward mean: 0.759517
- Reward margin mean: 0.240483

## Loser Visual Audit

- CSV: `reports/dpo_smoke_v7/loser_visual_audit.csv`
- JSONL: `reports/dpo_smoke_v7/loser_visual_audit.jsonl`
- Summary: `reports/dpo_smoke_v7/loser_visual_audit_summary.md`
- Reviewed losers: 10 / 10
- DPO-ready reviewed losers: 10 / 10

## GPU Blocker

The authorized GPU set is physical GPU4-7. Safe GPU status showed GPU4, GPU5, GPU6, and GPU7 were occupied by unrelated/unknown tasks at launch time. A single-GPU launch was prepared only after checking GPU6, but GPU6 reported about 9884 MiB used before launch and the run was blocked. GPU0-3 were not used.

Decision: `BLOCKED_GPU_BUSY_SUBSET_READY`. Do not start DPO until an authorized GPU is actually free. Do not use GPU0-3.

## Not Run

No DPO optimizer step, checkpoint save, checkpoint rollout, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or checkpoint modification was performed.
