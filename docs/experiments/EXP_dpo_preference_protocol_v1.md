# EXP DPO Preference Protocol v1

Updated: 2026-06-28T00:20:04

Status: COMPLETE_FOR_PAIR_GENERATION.

## Hypothesis

The previous DPO failure was caused by weak/ambiguous preference pairs. A stable pair protocol with clean GT winners, local corruptions, medium-hard rollout losers, and explicit quality floors should provide better DPO input than direct rollout ranking.

## Variables

Only the preference-pair generation protocol changes. No DPO training is run.

## Data

- Prefix condition: frames 0-4
- Target future: frames 5-80
- Base pairs: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- New manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`

## Pair Sources

- Type A: LocalDPO-style clean GT future vs local corrupted GT future.
- Type B: clean GT future vs quality-floor-passing medium-hard rollout.
- Type C: not used in v1 because no rollout winner currently passes a strong enough absolute-quality gate.

## Success Gate

- At least 50 valid V2V-5 pairs.
- No collapsed losers.
- Prefix untouched.
- Future-only winner/loser comparison.
- Medium-hard loser criteria recorded.
- Pair audit and contact sheets generated.

## Result

- Total valid pairs: 66
- Type A: 50
- Type B: 16
- Type C: 0

Gate: PASS for pair generation, not for training automation.

## Next Step

Run a full real-energy audit on the selected Type A subset, then test SDPO/Linear-DPO-style objectives without scaling until winner improvement is measurable.
