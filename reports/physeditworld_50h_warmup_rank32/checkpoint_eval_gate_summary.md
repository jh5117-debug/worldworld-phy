# PhysEditWorld Checkpoint Eval Gate Summary

Decision: `CHECKPOINT_EVAL_BLOCKED_EVAL_MANIFEST_MISSING`

- Status: `BLOCKED`
- Error reason: eval manifest missing
- Eval manifest: `manifests/physeditworld_50h_lingbot_val.jsonl` rows=None
- Checkpoint root: `local_assets/physeditworld_50h_warmup_rank32`
- Steps: `0,500,1000,2000`
- CUDA_VISIBLE_DEVICES: `4`
- GPU policy: `GPU_POLICY_PASS`

This gate does not perform image-only or prefix_len=1 fallback. True rollout, metrics, and Codex visual audit are required before any warm-up checkpoint can pass.
