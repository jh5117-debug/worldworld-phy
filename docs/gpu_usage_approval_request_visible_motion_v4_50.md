# GPU approval request: visible-motion v4 50-sample review

The v4 16-sample smoke passed numerically: 16/16 generated, 16/16 suitable, 0 too_static, 0 too_extreme, 0 delayed.

Recommended next step, if human review confirms the videos look better: run a 50-sample v4 review set before any 200/1k expansion.

Proposed command, only if approved:

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v4_stronger_start0_review \
  --templates drop collision roll containment \
  --template_counts drop:15,collision:15,roll:10,containment:10 \
  --num_trials 50 \
  --out local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v4_stronger_start0_review_50.jsonl \
  --dry-run --diverse_scene_seeds true --unique_source_configs true

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion_v4_stronger_start0_review \
  --plan local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v4_stronger_start0_review_50.jsonl \
  --out_root local_assets/data/physion/generated_v3 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

Approval needed: GPU0 / DISPLAY=:8. Do not run 200/1k from v4 until 50-sample human review passes.
