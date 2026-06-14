# TDW / Physion-style Moving-Camera v2 Generation Spec

## Terminology

Physion is TDW/ThreeDWorld simulation. v2 data should be called Physion-style TDW moving-camera simulation or Physion/TDW simulated clean GT. It is not real-world data.

## 2026-06-14 v5 Aggressive 2x 1000 Dataset

The current preferred warmup dataset is generated under `generated_v3`, not `generated_v2`:

- Profile: `warmup_visible_motion_v5_aggressive_2x_demo`.
- Total samples: 1000.
- New 800 generation root: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_1k_scaleup_800samples/`.
- Combined LingBot manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest.jsonl`.
- Split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits/`.
- Review pack: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_1000/`.

The v5 aggressive 2x profile was selected after human review because earlier visible-motion datasets were too static or visually insufficient. Camera motion starts at frame 0, and `use_action=false` remains required.

## Output Structure

`local_assets/data/physion/generated_v2/`

- `raw_hdf5/`
- `videos/`
- `contact_sheets/`
- `manifests/`
- `lingbot_cam_inputs/`
- `reports/`
- `logs/`

## Profile 1: warmup_mild

Purpose: LingBot-Fast camera-conditioned warmup.

Requirements:

- smooth camera motion;
- small/medium yaw and translation;
- target object visible ratio >= 0.75;
- foreground should not leave frame for long;
- avoid extreme lookaway and `relative_yaw_180_reobserve`;
- camera motion can begin before/during physics event, but should not hide main object;
- suggested max yaw: 10-25 degrees;
- output RGB, depth, ID, camera_pose, intrinsics/projection, object_state, and prompt.

Explicit camera set:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

These are the only variants allowed in `warmup_mild`. The wrapper rejects lookaway, offscreen, reobserve, relative-yaw-180, occluder, and extreme camera terms before generation.

Upstream mapping:

- orbit uses `camera_motion=orbit` and `camera_orbit_degrees=+/-12`;
- strafe uses `camera_motion=strafe` and `camera_strafe_distance=+/-0.25`;
- dolly uses the existing orbit/radius path with `camera_radius_delta=+/-0.10`.

## Profile 2: train_moderate

Purpose: later reward/DPO pair pool.

Requirements:

- moderate camera motion;
- target object visible ratio >= 0.6;
- allow some offscreen frames but reject complete disappearance;
- broader camera diversity than warmup.

## Profile 3: stress_reobserve

Purpose: test/stress split only.

Requirements:

- lookaway/offscreen/relative_yaw_180_reobserve allowed;
- object may leave frame but must reappear;
- target must be visible in first and reobserve segments;
- used for R_reobs and evaluation, not warmup main data.

## Profile 4: camera_only_static

Purpose: camera-following and rigid-background consistency tests.

Requirements:

- minimal foreground motion;
- camera moves;
- background should remain rigid and stable;
- good for R_bg and R_cam audits.

## Filtering Rules

Reject or mark as stress-only if:

- target_visible_ratio below profile threshold;
- target area too small;
- target disappears for too many consecutive frames;
- camera motion magnitude exceeds profile limits;
- camera jerk is too high;
- object completely offscreen for warmup;
- HDF5 keys incomplete;
- depth / ID / camera / object_state unavailable;
- frame count or duration invalid.

Every stage should output a validation report, contact sheet, storage estimate, and generation speed.

## Current Mild-Smoke Status

The `warmup_mild` plan dry-run is valid and contains no stress/reobserve
variants. The wrapper includes a display guard: a generation command must
specify or inherit a display whose GPU is either detected as GPU6/7 or
explicitly approved by the user. Unknown displays and GPU0-bound displays are
blocked by default.

One explicitly approved GPU0-bound `DISPLAY=:8` sample has now passed HDF5
validation:

- `drop` template;
- `orbit_left_12` camera;
- 83 frames;
- target visible ratio `1.0`;
- max invisible frames `0`;
- camera path length `0.5927`;
- RGB/depth/id/camera/object state present.

The sample is suitable as a TDW clean-GT warmup candidate at the HDF5 level.
The LingBot cam-only conversion is partial until `target.mp4` is
probe-confirmed. Do not proceed to 10/50/200/1k without the staged gate and
separate GPU approval if using `DISPLAY=:8`.
## 2026-06-04 10-Sample Smoke Observation

`warmup_mild` camera selection behaved as intended in the approved 10-sample smoke:

- no stress/reobserve camera variants were generated;
- target visibility stayed at 1.0 for all samples;
- max invisible frames was 0;
- camera variants covered orbit, strafe, and dolly mild motions.

However, template coverage did not match the dry-run request. The upstream execution produced only `drop` templates. The v2 wrapper should add a template coverage check before 50-sample validation or larger generation.

Suggested added validator:

- compare requested template distribution vs generated template distribution;
- fail or warn if non-drop templates are missing;
- require user confirmation before expanding a drop-only batch.

## 2026-06-03 Template-Diverse Execution Update

The v2 wrapper now implements the requested template coverage behavior:

- `plan_trials --template_counts drop:3,collision:3,roll:2,containment:2`;
- `run_tdw_trial --plan <manifest>` executes one upstream command per manifest row;
- output directories include template names;
- validation and LingBot conversion can filter by manifest.

Required template-diverse 10-sample command shape:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

This command must not be run unless the user approves GPU0 `DISPLAY=:8` for this specific template-diverse 10-sample smoke, or a GPU6/7 TDW display is available.

## 2026-06-04 Template-Specific Args Rule

The first approved template-diverse actual run showed that command-line arguments must be template-specific.

Rule:

- `drop` may receive `--drop`, `--ymin`, `--ymax`, and `--dscale`;
- `collision`, `roll`, and `containment` must not receive those drop-only arguments;
- common mild camera arguments may still be shared.

The wrapper now implements this rule. The next actual template-diverse 10-sample smoke should use the same manifest but the fixed command builder.

## 2026-06-04 Execution Flag Requirement

The upstream runner must receive:

```text
--run 1
```

Without this flag, `tdw_physion_multi_template_moving_camera.py` can exit successfully without writing HDF5, because actual generation is guarded by `if bool(args.run)`.

v2 wrapper requirements:

- all actual TDW commands must include `--run 1`;
- dry-run command reports must explicitly show whether `--run 1` would be passed;
- validation must treat command return code `0` without HDF5 as a failed generation, not as accepted data;
- template-diverse 10 cannot run until non-drop actual HDF5 validation passes.

## 2026-06-04 Non-Drop HDF5 Requirement

The fixed `--run 1` non-drop smoke showed that successful upstream exit is not enough.

Additional v2 acceptance rule:

- for every planned row, the runner must record a concrete HDF5 path;
- `returncode=0` with `hdf5=None` is a failed sample;
- expected `temp.hdf5` paths that do not exist are failed samples;
- template-diverse 10 must be blocked if any required non-drop template cannot write HDF5.

Current non-drop blocker:

`collision`, `roll`, and `containment` all return `0` but write no HDF5 under the current random single-sample invocation. The wrapper must either supply the required upstream template-specific parameters/stimuli or use an upstream-supported non-drop generation entry point before larger generation.

## 2026-06-04 Resolved Non-Drop Output Path Rule

The non-drop HDF5 blocker was traced to output path resolution, not to template inability.

Specification update:

- all per-trial `--dir` values passed to upstream TDW must be absolute paths;
- wrapper execution may use upstream Physion as `cwd`, so relative project paths are forbidden for upstream `--dir`;
- per-trial output directories must be created before subprocess launch;
- `returncode=0` with HDF5 written outside the project output tree is still a wrapper failure;
- manifest-specific validation files should be selected by suffix, for example `plan_warmup_mild_template_diverse_10_fix.jsonl` -> `validation_template_diverse_10_fix.json`;
- video probe must work without system `ffprobe` by falling back to `imageio` when needed.

Validated status:

- non-drop 3-sample: passed;
- template-diverse 10: passed;
- LingBot conversion: passed;
- 50-sample remains approval-gated.

## Template-Diverse 50-Sample Validation Status

The user approved one GPU0-bound `DISPLAY=:8` template-diverse 50-sample validation run. The v2 profile and filtering rules behaved as intended.

Planned distribution:

- `drop:15`
- `collision:15`
- `roll:10`
- `containment:10`

Actual validated status:

- generated HDF5: 50;
- validation OK: 50;
- rejected: 0;
- template distribution matched the plan;
- RGB/depth/ID/camera/object state completeness: 50/50;
- target visible ratio: 1.0 for all samples;
- max invisible frames: 0 for all samples;
- camera path length avg/min/max: 0.3682 / 0.1005 / 0.8888;
- LingBot cam-only conversion: 50/50;
- `target.mp4` probe: 50/50;
- `use_action=false`: 50/50;
- dummy action norm: 0.0 for every sample.

The 50-sample validation supports the `warmup_mild` profile as a candidate source for later LingBot-Fast camera warmup. It does not authorize automatic 200/1k generation or any training. The next stage is a separate 200-sample pilot approval, or a decision to pause data generation and return to the DPO signal gate.

## Warmup Visible-Motion Profile

Manual review showed `warmup_mild` is too static for the main camera-conditioned warmup split. A stronger non-stress profile has been added:

`warmup_visible_motion`

Allowed variants:

- `orbit_left_24`
- `orbit_right_24`
- `orbit_left_28`
- `orbit_right_28`
- `strafe_left_050`
- `strafe_right_050`
- `dolly_in_025`
- `dolly_out_025`

This profile remains separate from `stress_reobserve`. It bans lookaway, offscreen, reobserve, relative-yaw-180, occluder, and extreme motions.

Visible-motion acceptance thresholds:

- `target_visible_ratio >= 0.75`
- `max_invisible_frames <= 8`
- `camera_path_length >= 0.45`
- `camera_path_length <= 1.50`
- `background_motion_proxy >= 0.012`
- `video_motion_proxy >= 0.015`

Validator outputs:

- `too_static`
- `too_extreme`
- `suitable_for_visible_motion`

Dry-run status:

- 10-sample plan passed;
- template distribution is `drop:3`, `collision:3`, `roll:2`, `containment:2`;
- stress/reobserve `bad_count=0`.

Actual status:

- not run, because no GPU6/7 TDW display is available;
- GPU0-bound `DISPLAY=:8` was not used.
## 2026-06-05 warmup_visible_motion GPU0 Smoke Notes

`warmup_visible_motion` was tested with explicit user approval on GPU0-bound `DISPLAY=:8`.

Observed result:

- one-sample smoke passed;
- 10 / 10 generated HDF5 and passed key/visibility validation;
- 5 / 10 passed the visible-motion quality gate;
- 2 / 10 were too static (`dolly_in_025`, `dolly_out_025`);
- 3 / 10 were too extreme by camera-path threshold (one `collision_orbit_right_28`, two containment orbit samples).

Spec implication:

- visible-motion validation must be treated as a quality gate distinct from HDF5/key completeness;
- `suitable_for_visible_motion=true` is required for accepted warmup candidates;
- conversion with `--only_accepted true` must not convert samples rejected as `too_static` or `too_extreme`;
- before a 50-sample visible-motion run, revise the profile or per-template camera mapping.

Recommended next profile revision:

- keep `orbit_left/right_24` for drop-like scenes;
- keep `strafe_left/right_050` when target framing remains acceptable;
- remove or increase dolly beyond 0.25 only after a separate one-sample test;
- reduce containment orbit strength or add a per-template camera-path threshold after visual review.

## 2026-06-05 warmup_visible_motion_v2 Spec Addendum

`warmup_visible_motion_v2` introduces template-aware camera selection through:

```text
template_camera_variants
```

This is required because a single global camera cycle caused systematic v1 failures:

- roll received dolly variants that were too static;
- containment received orbit 24 variants that were too extreme;
- collision received orbit 28, which exceeded the path threshold.

v2 planned mapping:

| Template | Camera variants |
|---|---|
| drop | `orbit_left_24`, `orbit_right_24`, `orbit_left_28`, `orbit_right_28` |
| collision | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` |
| roll | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` |
| containment | `orbit_left_18`, `orbit_right_18`, `orbit_left_20`, `orbit_right_20`, `strafe_left_050`, `strafe_right_050` |

The validator thresholds remain unchanged. v2 actual validation is still required before requesting any 50-sample run.

## 2026-06-06 warmup_visible_motion_v2 Actual Result

The v2 actual 10-sample smoke has passed with the unchanged visible-motion thresholds.

Observed metrics:

- generated HDF5: 10 / 10;
- validation OK: 10 / 10;
- suitable for visible motion: 10 / 10;
- target visible ratio: 1.0 for every sample;
- camera path length min/avg/max: 0.5016 / 0.9790 / 1.3831;
- background motion proxy min/avg/max: 0.0120 / 0.0204 / 0.0295;
- `too_static`: 0;
- `too_extreme`: 0.

This confirms the template-aware camera mapping should be used for the next visible-motion validation stage. A 50-sample run still requires explicit user approval and must not be followed by 200 / 1k automatically.

## 2026-06-06 warmup_visible_motion_v2 50-Sample Result

The explicitly approved `warmup_visible_motion_v2` 50-sample validation completed successfully.

Observed result:

- planned distribution: `drop:15`, `collision:15`, `roll:10`, `containment:10`;
- generated HDF5: `50 / 50`;
- validation OK: `50 / 50`;
- suitable for visible motion: `50 / 50`;
- rejected: `0 / 50`;
- `too_static`: `0`;
- `too_extreme`: `0`;
- target visible ratio: `1.0` for every sample;
- max invisible frames: `0` for every sample;
- camera path length min/avg/max: `0.5016 / 1.0778 / 1.4814`;
- background motion proxy min/avg/max: `0.0121 / 0.0211 / 0.0332`.

Spec implication:

- `warmup_visible_motion_v2` should replace `warmup_mild` as the candidate camera-conditioned warmup data profile.
- The old `warmup_mild` 50-sample run remains useful as a pipeline validation set, but not as final warmup main data.
- Accepted visible-motion samples must satisfy both HDF5/key/visibility validation and the visible-motion quality flags.
- A 200-sample pilot is the next data-scale step, but it requires explicit user approval and must not cascade into 1k+ generation automatically.

## 2026-06-06 Spec Addendum: v3 start0 scene diversity and human-review gate

Human review can override a numeric pipeline pass. The v2 50-sample set remains pipeline-valid, but it is not final warmup main data because humans judged the motion and scene diversity insufficient.

`warmup_visible_motion_v3_start0_scene_diverse` adds:

- `camera_motion_start=0`;
- full-clip motion through frame 80;
- stronger template-aware camera values;
- no dolly variants;
- per-trial scene seeds;
- scene hash validation;
- early-motion metrics and `delayed_camera_motion`.

The v3 50-sample review result:

- HDF5/key validation: `50 / 50`;
- unique scene hashes: `50 / 50`;
- accepted for visible-motion v3: `28 / 50`;
- rejected: `22 / 50`;
- all rejected samples were strafe variants flagged as `too_static` and `delayed_camera_motion`;
- orbit variants passed without `too_extreme`.

Spec implication:

- `suitable_for_visible_motion_v3=true` is required before conversion/use as warmup data;
- `generated_v3` review data must not be promoted to main warmup data unless the human-review and early-motion gates pass;
- the next profile revision should either strengthen strafe or remove strafe from the accepted candidate camera set;
- no 200 / 1k generation should run from this v3 revision.

### Human-review acceptance note

The user subsequently reviewed the v3 videos and accepted all 50 as usable. This means the strict early-motion numeric rejection is not a hard data exclusion for this batch.

Spec implication:

- keep `too_static` and `delayed_camera_motion` in reports as diagnostics;
- allow human review to promote a sample when HDF5/key/visibility/scene-diversity gates pass;
- for this v3 50 set, all 50 samples are human-accepted and converted;
- future 200-sample runs still require explicit approval.

## 2026-06-07 Spec Note: v3 200 pilot result

The approved v3 200 pilot completed with:

- HDF5/key validation: `200 / 200`;
- unique scene hashes: `200 / 200`;
- target visibility: `1.0` for all samples;
- max invisible frames: `0`;
- conversion: `200 / 200`;
- `use_action=false` and dummy `action.npy` for all converted samples.

Numeric early-motion diagnostics are retained:

- numeric `suitable_for_visible_motion_v3`: `116 / 200`;
- `too_static` / `delayed_camera_motion`: `84 / 200`;
- `too_extreme`: `0 / 200`.

The numeric diagnostics should be reviewed alongside the video gallery. They should not silently block the human-accepted v3 profile, but they should remain visible before any 1k-scale request.

## 2026-06-07 Spec Note: v4 stronger start0 smoke

`warmup_visible_motion_v4_stronger_start0_review` was added as a stronger visible-motion review profile.

Changes versus v3:

- keeps camera motion start at frame 0;
- increases drop orbit to `36/40` degrees;
- uses stronger non-drop orbit: collision `32`, roll `30`, containment `22`;
- replaces weak strafe `0.55/0.65` with strafe `0.90` probes;
- keeps dolly disabled;
- tightens the minimum total camera path to `0.85` and first-8-frame path to `0.085`.

The 16-sample smoke passed numerically: `16 / 16` suitable, `0` too_static, `0` too_extreme, `0` delayed. Human review should decide whether v4 should replace v3 for the next 50-sample review.
## 2026-06-09 TDW v5 200 Dataset Promotion Note

The v5 aggressive 2x 200 dataset is human-approved as the current main camera-conditioned warmup candidate.

Promotion status:

- generated/conversion path: passed previously;
- manifest/audit/split: passed on 2026-06-09;
- LingBot dataloader smoke: passed;
- model-load forward-loss: not yet passed, only placeholder no-model-load tensor smoke passed.

This dataset is ready for a real LingBot-Fast model-load forward-loss smoke. It is not yet approved for training, Stage1, DPO, rollout, reward calibration, or checkpoint creation.

## 2026-06-09 Spec Note: v5 Data Passed True Forward-Loss Gate

The v5 aggressive 2x 200 dataset passed the true model-load forward-loss smoke.

Spec implications:

- v5 remains the active warmup dataset candidate;
- `use_action=false` and dummy zero `action.npy` remain required;
- camera conditioning must continue through poses/intrinsics-derived Plücker/control tensors;
- future warmup reports must log timestep, sigma, and noise band;
- if exact Fast expert routing is unavailable, high/low labels must be marked as diagnostic scheduler quantiles;
- no DPO or reward pair generation should start before a small warmup pilot is approved and evaluated.

The true forward smoke used one sample with latent shape `[16, 2, 60, 104]` and camera control shape `[1, 384, 2, 60, 104]`; all logged losses were finite.

## 2026-06-09 Stage A Warmup Pilot Note

The TDW v5 aggressive 2x 200 dataset has now passed a minimal LingBot-Fast Stage A high-noise warmup pilot:

- `staged_warmup_pilot` completed 20 steps;
- train losses were finite, 0.030702 to 0.062314;
- validation forward losses were finite, 0.033537 and 0.034270;
- latent shape remained `[16, 2, 60, 104]`;
- camera/control shape remained `[1, 384, 2, 60, 104]`;
- dummy action norm was `0.0`;
- runtime LoRA trainable params: 40,960;
- LoRA targets: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- sampled base parameters were unchanged;
- no checkpoint, LoRA, optimizer state, rollout, reward calibration, DPO, or new TDW generation was produced.

This validates the model-side warmup path, not the data-generation profile. The next warmup run should shuffle or balance templates because the first 20 train rows used in this pilot were all `collision + orbit_right_64`.

## 2026-06-09 Spec Note: Balanced Stage A Warmup Pilot

The TDW v5 aggressive 2x 200 dataset remains the current human-approved camera-conditioned warmup dataset. No new TDW data was generated in this gate.

Balanced Stage A high-noise warmup passed:

- balanced sampler over `template,camera_variant`;
- `60 / 60` train steps;
- train templates: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- diagnostic timestep / sigma: `799 / 0.799`;
- latent shape: `[16, 2, 60, 104]`;
- camera/control shape: `[1, 384, 2, 60, 104]`;
- dummy action norm: `0.0`;
- train losses finite;
- val losses finite;
- LoRA trainable params: `40,960`;
- sampled frozen base parameters unchanged.

The run saved exactly one adapter-only checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Size: `166,809` bytes. No full model weights or optimizer state were saved.

The next review should be a tiny approved rollout smoke, one sample per template, comparing base LingBot-Fast against the Stage A adapter. DPO and reward pair selection remain later gates.
## 2026-06-10 v5 Data / Rollout Gate

The v5 aggressive 2x 200 human-approved dataset is the current main warmup candidate. It should not be superseded by larger generation until rollout and reward gates show that the model benefits from the Stage A camera adapter.

No TDW scale-up was run in this pass because a GPU4-7 TDW display was not confirmed and GPU0 TDW generation was not approved. The next TDW generation decision is explicit: approve GPU0 `DISPLAY=:8`, configure GPU4-7 display, or defer scale-up.

The code now supports using the balanced Stage A adapter checkpoint for LingBot-Fast rollout comparison. Reward-pair construction remains downstream of rollout and reward confidence.

## 2026-06-10 4-Condition Base vs Adapter Rollout Note

The v5 aggressive 2x 200 dataset has now been used for a small approved rollout comparison:

- one condition per template;
- base videos: 4/4;
- Stage A adapter videos: 4/4;
- GT/base/adapter probe: 12/12;
- gallery: `local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`.

The adapter runtime import path was fixed by passing the project root into the generated LingBot runtime subprocess. No TDW generation, reward scoring, pair construction, DPO, VideoGPA `03_train`, Stage1, or training was performed.

## 2026-06-10 Reward Scoring Note for 4-Condition Rollout

Reward v5 scoring has now been run on the existing 4-condition GT/Base/Stage-A-adapter rollout. No new TDW generation, rollout, training, DPO, VideoGPA `03_train`, Stage1, or reward calibration was performed.

Scores:

- GT avg: `0.492143`;
- Base avg: `0.294709`;
- Stage A adapter avg: `0.295647`;
- Adapter > Base: `2/4`;
- GT > generated: `4/4`.

Pair construction is blocked because backend confidence is below the required threshold:

- generated reward confidence avg: `0.463235`;
- generated real-backend confidence avg: `0.411765`;
- `R_reobs` missing;
- generated reward components fallback-heavy.

Spec implication: TDW v5 remains the active warmup dataset, but the current 4-condition reward output is diagnostic only. It must not be used for DPO until reward confidence and pair margins improve.

## 2026-06-12 Moving-Camera Dataset Usage Note

The TDW v5 aggressive 2x 200 set remains the current main camera-visible warmup dataset.

The next gate used the existing v5 200 data rather than generating 1k new samples:

- no GPU4-7 TDW display was available;
- no GPU0 TDW 1k approval was active;
- no new TDW data was generated.

Warmup and rollout:

- Stage A and Stage B adapter warmups completed.
- Base / Stage A / Stage B generated `12/12` rollout videos each on 12 held-out conditions.

Reward/pair status:

- reward scoring completed;
- reward confidence did not pass the DPO pair threshold;
- pair count is `0`;
- DPO is not ready.

Spec implication: v5 data is usable for warmup experiments, but DPO remains gated by reward confidence and pair quality, not by TDW generation alone.
