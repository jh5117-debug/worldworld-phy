# PhysEditWorld Tiny Anchored DPO Gate Summary

Decision: `TINY_DPO_BLOCKED_INSUFFICIENT_PAIRS`

- Status: `BLOCKED`
- Error reason: pair rows 0 < 100
- Pair manifest: `manifests/physeditworld_dpo_pairs_anchored_v0.jsonl` rows=0
- Pair gate decision: `UNKNOWN`
- Minimum pairs: `100`
- Requested steps: `200`
- CUDA_VISIBLE_DEVICES: `4`
- GPU policy: `GPU_POLICY_PASS`

No tiny DPO is allowed until at least 100 reviewed anchored pairs exist and the pair gate has passed.
