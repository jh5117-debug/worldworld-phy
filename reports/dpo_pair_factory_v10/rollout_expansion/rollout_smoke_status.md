Current Status:
V10_ROLLOUT_SMOKE_BLOCKED_POLICY_INIT

# DPO Pair Factory v10 Rollout Smoke Status

A one-condition C-camera-self-temporal-r4 rollout smoke was attempted on physical GPU7 using `cam_physgeo.eval.run_v2v5_inference` and `manifests/dpo_pair_factory_v10_rollout_C_smoke.jsonl`.

The process reached:

- `[v2v5] run start`
- `[v2v5] import wan`
- `[v2v5] wan imported`
- `[v2v5] instantiate WanI2VFast`

It did not reach shard loading, LoRA loading, GPU forward, or video generation within the bounded observation window. GPU7 memory stayed near-zero, while CPU RSS rose above 20GB, indicating CPU-side runtime/model initialization rather than rollout generation.

Decision:
- Do not launch expanded 32/64/70-condition rollout until the runner init path is bounded or reused from a known-good persistent runtime.
- Existing strict DPO-ready pair count remains 18.
- Condition pool remains ready with 102 runnable prefix5 conditions.

Not run:
- No DPO / SDPO / Linear-DPO / Safe-linear.
- No StageA / StageB / GRPO / broad-LoRA.
- No checkpoint or weight modification.
- No media pushed.
