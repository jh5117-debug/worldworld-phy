<!-- RUN_RESULTS:START -->
## Run Results

Current Status: PASS

- Total v10 pairs audited: 81.
- Strict ready / trainable: 81.
- Diagnostic-only: 0.
- Rejected: 0.
- Rollout-derived trainable: 15.
- Synthetic controlled trainable: 63.
- TypeA_plus controlled: 3.
- Top50 balanced manifest: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`.
- Data card: `docs/dpo_pair_factory_v10b_data_card.md`.
- PPT slide notes: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10b_slide_notes.md`.
- No training, DPO, SDPO, Linear-DPO, winner-anchor, rollout, StageA, StageB, GRPO, or broad-LoRA was run.
<!-- RUN_RESULTS:END -->

Current Status:
PAIR_FACTORY_V10B_PRD_READY

# EXP: DPO Pair Factory v10b Final Audit / Data Freeze

## Current Status
- v10 ready pairs = 81.
- existing strict ready = 18.
- synthetic visible TypeM-v10 = 63.
- real rollout expansion remains blocked by WanI2VFast initialization.
- PPT showcase is ready.

## Problem
The 81-pair pool exceeds the 50-pair data gate, but pair sources are mixed. Controlled synthetic negatives must not be described as real model rollout losers. Future DPO smoke, paper positioning, and meeting slides need clean subsets and a data card.

## Hypothesis
Synthetic controlled pairs are useful for anchored / LocalDPO-style controlled negative learning. Real rollout-derived pairs are closer to the model distribution but still too few. A balanced top50 can support a future tiny anchored DPO smoke, while rollout-only must remain a smaller analysis subset until real rollout expansion is fixed.

## Inputs
- `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`
- `manifests/dpo_pair_factory_v10_synthetic_visible_pairs.jsonl`
- `manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl`
- `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_selected_pairs.csv`

## Audit Rule
Every pair is checked for source type, schema completeness, shared condition, prefix length, future-frame range, video path availability, Codex visual audit flags, reward margin or synthetic severity justification, and clear failure label. Synthetic pairs are never relabeled as rollout-derived pairs.

## Success Gate
- Pair cards are written for all 81 pairs.
- all-ready, rollout-only, synthetic-only, top50, top20-demo, and PPT subset manifests are produced.
- Data card states the synthetic caveat clearly.
- Reports distinguish trainable, diagnostic-only, and rejected pairs.

## Failure Gate
- Missing/undecodable videos cannot be repaired from manifest metadata.
- Source type cannot be determined.
- Pair lacks visual audit or written reason.
- Pair is too subtle, too blurry, collapsed, or winner-bad.

## Outputs
- `reports/dpo_pair_factory_v10b/pair_card.csv`
- `reports/dpo_pair_factory_v10b/pair_card.jsonl`
- `manifests/dpo_pair_factory_v10b_ready_all.jsonl`
- `manifests/dpo_pair_factory_v10b_ready_rollout_only.jsonl`
- `manifests/dpo_pair_factory_v10b_ready_synthetic_controlled.jsonl`
- `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`
- `manifests/dpo_pair_factory_v10b_top20_demo.jsonl`
- `manifests/dpo_pair_factory_v10b_ppt_subset.jsonl`
- `docs/dpo_pair_factory_v10b_data_card.md`
- `docs/dpo_pair_factory_v10b_report.md`

## What Is Explicitly Not Run
- No DPO training.
- No SDPO / Linear-DPO / Safe-linear.
- No winner-anchor.
- No rollout or inference.
- No checkpoint eval.
- No StageA / StageB / GRPO / broad-LoRA.
- No deletion of data, checkpoints, or weights.
- No media/local_assets commit.

## Git Checkpoints
- Before execution: commit PRD/status.
- After audit/subset build: commit source, tests, manifests, reports.
- After docs/data card: commit documentation.
