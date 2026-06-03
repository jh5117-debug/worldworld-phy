# GPU Usage Approval Request: TDW Template-Diverse 10-Sample Smoke

Date: 2026-06-03

## Request

Approve one TDW / Physion-style `warmup_mild` template-diverse 10-sample smoke using the current GPU0-bound `DISPLAY=:8`.

## Why Approval Is Needed

The previously approved GPU0 runs covered:

- one 1-sample warmup_mild smoke;
- one 10-sample warmup_mild smoke.

This is a new template-diverse 10-sample run. The current prompt did not grant a new GPU0 approval. The only known TDW display remains:

```text
DISPLAY=:8
Xorg config: /etc/X11/tdw-xorg-gpu0.conf
Detected GPU: GPU0
```

Default gate/smoke policy prefers GPU6/7, but no GPU6/7 TDW display is currently available.

## Proposed Command If Approved

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_mild \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --dry-run

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

Validation and conversion after approval:

```bash
python -m cam_physgeo.data.tdw_generation_v2.validate_generated_hdf5 \
  --root local_assets/data/physion/generated_v2 \
  --manifest local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --out local_assets/data/physion/generated_v2/reports/validation_template_diverse_10.md \
  --make_contact_sheet

python -m cam_physgeo.data.tdw_generation_v2.convert_generated_to_lingbot \
  --root local_assets/data/physion/generated_v2 \
  --manifest local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --out local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse \
  --only_accepted true \
  --num_frames 81 \
  --fps 16 \
  --size 480x832 \
  --use_action false \
  --make_dummy_action true \
  --force_rewrite_video true \
  --probe_video true
```

## Expected Resources

| Item | Estimate / Constraint |
|---|---|
| GPU | GPU0 via `DISPLAY=:8` |
| Samples | exactly 10 |
| Duration | approximately similar to prior 10-sample run, about 20-25 minutes |
| Storage | roughly 0.8-1.0 GiB raw HDF5 plus derived videos/metadata |
| Risk | low technical risk, but uses GPU0 outside default GPU6/7 policy |

## Smaller Alternative

Run only a 4-sample template coverage smoke:

```text
drop:1, collision:1, roll:1, containment:1
```

This would verify non-drop templates with lower GPU0 time, but would not replace the requested 10-sample gate.

## Other Alternative

Configure or provide a GPU6/7 TDW display, then run the same command without GPU0 approval.

## Recommendation

Approve GPU0 `DISPLAY=:8` for exactly this 10-sample template-diverse smoke before any 50-sample validation.

