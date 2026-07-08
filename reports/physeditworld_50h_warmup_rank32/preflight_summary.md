# PhysEditWorld Warm-Up Gate Summary

Decision: `WARMUP_BLOCKED_EMPTY_MANIFEST`

- Status: `BLOCKED`
- Error reason: train manifest has zero rows
- Config: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
- Manifest: `manifests/physeditworld_50h_lingbot_train.jsonl` rows=0
- Val manifest: `manifests/physeditworld_50h_lingbot_val.jsonl` rows=None
- Gravity prompt-only: `True`
- LoRA rank: `32`
- CUDA_VISIBLE_DEVICES: `4`
- GPU policy: `GPU_POLICY_PASS`

This command is a safety gate for the PhysEditWorld 50h rank32 warm-up. It does not perform training unless prerequisites are present and the backend is explicitly connected in a later implementation.
