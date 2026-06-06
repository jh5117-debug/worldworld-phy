# GPU approval request: visible-motion v3 200-sample pilot

Task:

Run a 200-sample TDW / Physion-style `warmup_visible_motion_v3_start0_scene_diverse` pilot after the user manually accepted the v3 50-sample review set.

Current evidence:

- v3 50 HDF5 generation: `50 / 50`
- HDF5/key validation: `50 / 50`
- unique scene hashes: `50 / 50`
- human review acceptance: `50 / 50`
- LingBot cam-only conversion: `50 / 50`
- `use_action=false`: `50 / 50`
- dummy `action.npy`: `50 / 50`

Important diagnostic note:

The numeric validator marked 22 strafe samples as `too_static` / `delayed_camera_motion`, but the user reviewed the rendered videos and accepted them. Keep these metrics in reports, but do not treat them as hard rejects for the human-reviewed v3 profile.

Requested GPU/display:

- GPU0-bound `DISPLAY=:8`

Estimated storage/time:

- raw HDF5: about `16-18 GB`
- LingBot cam-only conversion: about `36-40 GB`
- runtime: roughly 7-9 hours on GPU0-bound TDW display, based on prior 50-sample runs

Proposed command:

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v3_start0_scene_diverse \
  --templates drop collision roll containment \
  --template_counts drop:60,collision:60,roll:40,containment:40 \
  --num_trials 200 \
  --out local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v3_start0_scene_diverse_200.jsonl \
  --dry-run \
  --diverse_scene_seeds true \
  --unique_source_configs true

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion_v3_start0_scene_diverse \
  --plan local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v3_start0_scene_diverse_200.jsonl \
  --out_root local_assets/data/physion/generated_v3 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

Approval required:

Do not run this 200-sample pilot until the user explicitly approves GPU0 / `DISPLAY=:8` for this exact task.

Not approved:

- 1k+ generation
- training
- DPO
- VideoGPA `03_train`
- Stage1
- reward calibration
- LingBot rollout
- checkpoint / LoRA save
