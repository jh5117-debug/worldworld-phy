# DPO Preference Protocol v1 Status

Updated: 2026-06-28T00:20:04

## Current State

This round did **not** train DPO. The goal was to build a stable, scalable V2V-5 preference-pair generation protocol after the prior tiny DPO probe failed.

## Why The Prior Probe Failed

The previous tiny DPO run used real LingBot-Fast energy and passed BF16 runtime checks, but it did not provide a useful preference signal:

- DPO loss stayed near `0.693`.
- Winner improvement was tiny and negative at the final step.
- DPO step20 videos were visually worse than StageA final and showed extra object fragments.

This indicates a pair/reward protocol problem, not a reason to keep training the same DPO setup.

## Protocol v1 Outputs

- Final pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- Total pairs: 66
- Valid pairs: 66
- Type A local corruption pairs: 50
- Type B GT vs medium-hard rollout pairs: 16
- Type C teacher/high-quality rollout pairs: 0
- Rollout pool count: 48
- Quality-floor pass count: 48
- Selected medium-hard rollout losers: 16

## Decision

Preference-pair generation protocol v1 is ready for review and small DPO planning, but DPO training should still wait for a full real-energy audit over the selected subset. Start with Type A pairs before adding Type B.

## Safety

No DPO trainer, StageB, GRPO, full-data long StageA, checkpoint deletion, or data/weight push was performed.
