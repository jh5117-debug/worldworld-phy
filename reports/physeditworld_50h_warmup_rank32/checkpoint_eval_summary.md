# PhysEditWorld Checkpoint Eval Gate Summary

Decision: `CHECKPOINT_EVAL_BLOCKED_EMPTY_EVAL_MANIFEST`

- Status: `BLOCKED`
- Error reason: eval manifest has zero rows
- Eval manifest: `manifests/physeditworld_50h_lingbot_val.jsonl` rows=0
- Eval manifest validation: `reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json` decision=`LINGBOT_MANIFEST_BLOCKED_EMPTY`
- Checkpoint root: `local_assets/physeditworld_50h_warmup_rank32`
- Steps: `0,500,1000,2000`
- CUDA_VISIBLE_DEVICES: `4`
- GPU policy: `GPU_POLICY_PASS`

This gate does not perform image-only or prefix_len=1 fallback. True rollout, metrics, and Codex visual audit are required before any warm-up checkpoint can pass.
