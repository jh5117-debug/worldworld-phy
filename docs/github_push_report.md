<!-- DPO_PAIR_FACTORY_V11_PUSH:START -->
## DPO Pair Factory v11 Scale-500

- Scope: docs, source/tests, manifest JSONL, CSV/JSON/MD summaries.
- Excluded: MP4/JPG/PNG/contact sheet images/local_assets/checkpoints/weights.
- Ready500 manifest: `manifests/dpo_pair_factory_v11_ready_500.jsonl`.
<!-- DPO_PAIR_FACTORY_V11_PUSH:END -->

<!-- DPO_PAIR_FACTORY_V10B_PUSH:START -->
## DPO Pair Factory v10b Final Audit

- Commit scope: docs, audit script/tests, small CSV/JSON/JSONL manifests, data card, slide notes.
- Excluded: MP4/JPG/PNG/local_assets/checkpoints/weights/large logs.
- Ready pairs: 81.
- Top50 manifest: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`.
<!-- DPO_PAIR_FACTORY_V10B_PUSH:END -->

# GitHub Push Report: v8n tiny objective diagnosis

Current Status:
V8N_BLOCKED_WINNER_ANCHOR_REPEAT_SIGNAL_FAIL

Commits pushed in this phase include the v8n PRD, pair-cache objective selector/runner, default config fix, and result documentation. Large files, videos, images, checkpoints, and local_assets were not staged for push.


<!-- V8M_GIT:START -->
## v8m Git Checkpoint

Built and validated reviewed pair cache v8m. Commit pending at generation time. Cache tensors remain under `local_assets/` and are not staged.
<!-- V8M_GIT:END -->

<!-- V8L_GIT:START -->
## v8l Git Checkpoint

Prepared v8l objective preflight. Decision: `V8L_BLOCKED_WINNER_ONLY_CACHE_NO_LOSER_ENERGY`. Commit pending at generation time.
<!-- V8L_GIT:END -->

Current Status Update (2026-07-03T09:42:30): V8K_RESULTS_PENDING_COMMIT

v8k cache-only winner-anchor PASS; preparing docs/small CSV/log commit. No checkpoint/video/weights are staged.

Current Status Update (2026-07-03T09:16:56): V8K_PRD_PENDING_COMMIT

v8k cache-only winner-anchor PRD/status prepared. No winner-anchor run has started yet in this commit.

Current Status Update (2026-07-03T09:15:05): V8J_RESULTS_PENDING_COMMIT

v8j cache10 build+validation PASS; preparing source/docs/small reports commit. Cache tensors in local_assets are not staged.

Current Status Update (2026-07-03T08:50:49): V8J_PRD_PENDING_COMMIT

v8j cache10 build+validation PRD/status prepared. No runtime cache build has started yet in this commit.

Current Status Update (2026-07-03T08:48:33): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-03T08:48:18): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-03T08:47:32): V8I_RESULTS_PENDING_COMMIT

v8i fast-init/full-condition first-row cache PASS. Preparing code/docs/small-report commit; local_assets and media/checkpoint files remain excluded.

Current Status Update (2026-07-02 22:03:10): V8G_COMMIT_READY_FOR_PUSH

- v8g result commit: `bef97c7` (`Run Wan from_pretrained split diagnosis v8g`).
- Branch: `research/quant-small-lora-dpo-probe-20260624`.
- Large files excluded: MP4/JPG/PNG/local_assets/checkpoints/weights.
- Next action: push current branch and verify remote head.

Current Status Update (2026-07-02 21:58:17): V8G_RESULTS_PENDING_COMMIT

v8g results are being prepared for commit/push. Large files, videos, images, checkpoints, and local_assets remain excluded.

Current Status:
V8F_PUSHED

# GitHub Push Report

Updated: 2026-07-02 19:31 CST

v8f PRD commit `9ab511a`, instrumentation commit `ababbb6`, and result commit `ae6b197` were pushed to `origin/research/quant-small-lora-dpo-probe-20260624`.

The v8f result commit includes docs, source/test update, small JSONL/markdown/CSV reports, and no videos/images/checkpoints/weights. Forbidden large artifacts were not added.


## v8h Update - 2026-07-03T06:46:04

Prepared v8h PRD in commit `815588e`. Added safe Wan policy loader instrumentation and v8h runtime/cache reports locally; final code/report commit pending after verification. No media/checkpoint/weights intended for commit.


<!-- dpo_pair_factory_v10_update -->
## DPO Pair Factory v10 Update

Current Status: PAIR_FACTORY_V10_READY_50_SYNTHETIC_MIXED

- Runnable prefix5 conditions recovered: 102.
- Existing strict DPO-ready pairs: 18.
- Synthetic visible TypeM-v10 ready pairs: 63.
- Combined ready pairs: 81.
- Combined manifest: `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`.
- Caveat: 63 new pairs are controlled synthetic visible negatives, not true rollout TypeB losers.
- No DPO / SDPO / Linear-DPO / StageA / StageB / GRPO / broad-LoRA was run.
<!-- /dpo_pair_factory_v10_update -->
