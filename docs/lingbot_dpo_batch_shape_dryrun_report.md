# LingBot DPO Batch Shape Dry-Run Report

## Result

- Status: passed.
- Pair id: `pair_2a77384981ab`
- Pair type: `gt_vs_fast_rollout`
- Reward margin: `0.5240882262358174`
- Output directory: `local_assets/outputs/smoke/lingbot_dpo_batch_dryrun/`
- Batch summary path: `local_assets/outputs/smoke/lingbot_dpo_batch_dryrun/batch_summary.json`

## Tensor Shapes

- Winner latent shape: `[16, 2, 60, 104]`
- Loser latent shape: `[16, 2, 60, 104]`
- Batch crop needed: no.
- Winner/loser batch dtype after collation: `bfloat16`
- Noise shape: `[16, 2, 60, 104]`
- Noise dtype: `bfloat16`
- Timestep shape/value: `[1]`, value `579`

## Same Noise / Same Timestep

- Same noise confirmed: true.
- Same timestep confirmed: true.
- Policy/reference condition is the same condition pack at this dry-run level.

## Condition

- Condition keys retained: `action`, `camera_motion`, `image`, `intrinsics`, `metadata`, `poses`, `prefix`, `prompt`, `sample_id`, `template`, `use_action`.
- Camera control tensor summary was present.
- `use_action=false` remained true.
- Dummy action norm remained `0.0`.
- `batch_ready_for_energy`: true at shape/condition-pack level.

## Not Training

No model forward, backward, optimizer, LoRA save, or parameter update was run.

