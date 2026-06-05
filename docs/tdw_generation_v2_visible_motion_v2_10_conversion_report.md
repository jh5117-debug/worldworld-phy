# TDW Generation v2 Visible-Motion v2 10-Sample Conversion Report

Date: 2026-06-05

## Status

Not run.

## Reason

The v2 actual generation did not run because remote SSH became unavailable while syncing code to the TDW helper worktree.

No v2 accepted samples exist yet, so there was nothing to convert.

## Next Step

After v2 actual generation and validation complete, convert only samples with:

```text
suitable_for_visible_motion=true
```

using:

```bash
python -m cam_physgeo.data.tdw_generation_v2.convert_generated_to_lingbot \
  --root local_assets/data/physion/generated_v2 \
  --manifest local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_10.jsonl \
  --out local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10 \
  --only_accepted true \
  --num_frames 81 \
  --fps 16 \
  --size 480x832 \
  --use_action false \
  --make_dummy_action true \
  --force_rewrite_video true \
  --probe_video true
```
