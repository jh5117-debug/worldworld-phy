
# DPO Preference Protocol v4 Report

Current Status: PASS_REWARD_GUIDED_PROTOCOL_READY_FOR_SMALL_SMOKE

Updated: 2026-06-30 12:09:54

## Summary

Protocol v4 builds reward-guided medium-hard V2V-5 preference pairs from existing prefix5 conditions. It does not train DPO and does not run StageB/GRPO/full-data StageA.

Final manifest: `manifests/dpo_preference_protocol_v4_pairs.jsonl`

Counts:

- Total training-ready pairs: 42
- TypeA_plus: 34
- TypeM: 8
- TypeB_usable: 0
- TypeC: 0
- DPO-ready JSONL: `reports/dpo_pair_hardness_v4/dpo_ready_pairs_v4.jsonl`

## What Changed From Protocol v3

Protocol v3 had 34 TypeA local-corruption pairs and 0 usable TypeB pairs. v4 keeps the clean prefix-aware schema but adds:

- TypeA+: stronger local corruption selected by reward, sharpness, and visual gates.
- TypeM: rollout-inspired synthetic medium-hard negatives that remain sharp and readable.
- Explicit blur penalty and subreward alignment gate.
- PPT-ready all-in-one showcase with WIN/LOSE, reward labels, affected-region zoom, and heatmap.

## TypeA+ Result

TypeA strength sweep evaluated 136 severity candidates and accepted 34 TypeA+ pairs. The accepted set uses `s4_strong_pass` where needed because weaker severities were usually too subtle under the reward-margin gate.

## TypeM Result

TypeM generated rollout-inspired synthetic failures and accepted 8 pairs. Failure modes include background drift, wrong camera motion, object identity instability, weak physical event, and extra-fragment style errors. This is below the desired 10-30 range, so TypeM should be expanded next, but the current set is useful for a small smoke.

## TypeB Result

TypeB remains blocked: previous rollout candidates are still diagnostic blur/quality failures. v4 keeps TypeB_usable at 0 and does not admit blurred rollout losers into the training-ready manifest.

## Metrics Backend

- PSNR: computed.
- SSIM: computed as global proxy for v4 generation tables.
- LPIPS: blocked/not run for full sweep tables.
- FVD: BLOCKED_BY_ENV.
- VBench: BLOCKED_BY_ENV.

## PPT Showcase

Main MP4: `reports/ppt_winlose_showcase_latest/winlose_showcase_reward_guided_v4_for_ppt.mp4`

Selected pair table: `reports/ppt_winlose_showcase_latest/reward_guided_v4_selected_pairs.csv`

Codex preview-frame review confirmed the labels are readable, WIN/LOSE are clear, reward text is legible, and heatmaps show localized differences. The first TypeM pair is the best reward-guided example; the first TypeA+ pair is the best LocalDPO/controlled-corruption example.

## Decision

Protocol v4 is ready for a next tiny DPO smoke, not for scale. Recommended first subset: 4 TypeA+ + 4 TypeM if TypeM diversity is acceptable, or 6 TypeA+ + 2 TypeM if prioritizing stability. Do not use TypeB rollout losers until candidate generation produces sharp, readable losers.
