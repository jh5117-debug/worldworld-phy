# Physion / TDW Large-Scale Generation Plan

This is a plan only. No TDW or Physion generation was run in this round.

## Can Large Generation Happen?

Yes, but only after the DPO and reward/camera gates remain stable and after a
small generation dry-run validates the TDW stack. The project should not jump
directly to a large batch because storage, HDF5 schema, camera convention, and
reward quality can fail silently at scale.

## Staged Rollout

1. 1 sample dry-run
   - Use a new output root.
   - Validate TDW launches, the template runs, and HDF5/RGB/depth/ID/camera
     outputs are written.

2. 10 sample smoke
   - Cover at least two templates and two camera motions.
   - Produce contact sheets and metadata summaries.

3. 50 sample validation
   - Check HDF5 keys, frame counts, depth, ID masks, camera poses, projection
     matrices, object states, prompt text, and converted intrinsics.

4. 200 sample pilot
   - Measure generation speed, storage, corruption/failure rate, camera motion
     distribution, and reward score distribution.

5. 1k+ batch
   - Only after user approval for storage, runtime, template list, and camera
     motion distribution.

## Per-Stage Checks

For every generated clip:

- RGB frames / MP4 readable.
- HDF5 keys readable.
- depth exists and is finite.
- ID mask exists and has object/background structure.
- camera pose exists for all frames.
- projection/intrinsics exist and convert to `[fx, fy, cx, cy]`.
- object state / contact metadata exists where template supports it.
- prompt exists.
- contact sheet saved.
- reward score can run on a small subset.
- storage cost and generation time recorded.

## Code Sources

- Official Physion / benchmark organization:
  `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021`
- TDW physics generation:
  `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/tdw_physics`
- Local moving-camera extensions:
  `/home/nvme03/workspace/physion_moving_camera_mainline_20260505`
- Existing active runtime assets:
  `local_assets/data/physion/`

## Output Root

Use only:

`local_assets/data/physion/generated_v2/`

Do not overwrite or mutate existing migrated Physion data.

## Required User Confirmations

- total clip count;
- templates/scenarios;
- camera motions;
- estimated storage budget;
- TDW CPU/GPU allocation;
- whether TDW license/runtime constraints are acceptable;
- whether generated data should include stress camera motions or balanced
  natural moving-camera motions.

## Gate Before Generation

Large generation is not allowed until:

- scalar DPO dry-run is understood;
- reward remains stable on real backends;
- camera condition is at least partially effective;
- TDW one-sample generation dry-run passes;
- user explicitly approves scale and storage.

## Generation Is Not Next Immediate Step Unless User Requests

The current DPO plumbing has only reached a 1-pair backward-only dry-run. It has
not reached a real optimizer-step dry-run, and it has not reached any training
loop. Therefore large TDW/Physion generation should not start automatically.

If the user wants to prepare data before the DPO training gate is complete, the
only allowed generation action should be a 1-sample generation dry-run. It must
write to a new output root and validate:

- HDF5 keys;
- RGB frames;
- depth;
- ID mask;
- camera pose;
- projection / intrinsics;
- object state;
- prompt;
- reward smoke score;
- contact sheet;
- storage size;
- generation runtime.

The staged plan remains:

1. 1 sample dry-run.
2. 10 sample smoke.
3. 50 sample validation.
4. 200 sample pilot.
5. 1k+ only after explicit storage/runtime/template approval.

Generation sources remain:

- official Physion / `physics-benchmarking-neurips2021`;
- `tdw_physics` / TDW;
- project moving-camera extension scripts.


## Generation v2 Gate Dependency Update

Large-scale TDW / Physion-style generation is not the immediate next step unless explicitly requested. The project is currently at the staged generation-spec and partial-smoke stage. v2 generation must remain staged: 1 sample -> 10 samples -> 50 validation -> 200 pilot -> 1k+ only after user confirmation.

Warmup data must use mild/smooth camera motion and must reject clips where the target foreground disappears for too long. Strong reobserve and relative-yaw stress clips should remain in a stress/test split, not the main LingBot-Fast warmup split.

Current v2 blocker: the existing upstream batch runner does not expose an explicit mild-only camera-set option. Until this is added, warmup_mild actual generation should remain blocked rather than silently mixing stress/reobserve variants into warmup data.

## Mild Camera Set Patch Status

The v2 wrapper now defines an explicit `warmup_mild` set and runtime upstream mapping. The previous mild-only camera-set blocker is fixed at the planning/wrapper level:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

The warmup plan check produced `bad_count=0` for stress/reobserve keywords.

Actual TDW generation remains blocked by the display/GPU routing gate: the observed TDW display is likely bound to GPU0, while current smoke work only permits GPU6/7. Do not run 1/10/50 actual generation until a GPU6/7 display is available or the user explicitly approves the existing display.

## Display / GPU Routing Update

The current TDW display `:8` is bound to GPU0 through `/etc/X11/tdw-xorg-gpu0.conf`. Existing displays `:9` to `:13` are Xvfb / Mesa llvmpipe software displays; they are useful for lightweight display checks, but they do not prove TDW/Unity generation can run safely in CPU/headless mode.

No actual TDW sample should be generated until one of these happens:

1. a GPU6/7 TDW Xorg display is provided;
2. the user explicitly approves one GPU0-bound 1-sample smoke;
3. TDW headless/CPU mode is separately validated.

## GPU0 One-Sample Approval Result

The user approved exactly one GPU0-bound `DISPLAY=:8` `warmup_mild` smoke. The
first attempt failed before scene generation due wrapper startup issues; those
issues were fixed. The rerun produced one valid HDF5:

- HDF5:
  `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5`
- template / camera: `drop` / `orbit_left_12`
- target visible ratio: `1.0`
- max consecutive invisible frames: `0`
- camera path length: `0.5927`
- HDF5 completeness: RGB/depth/id/camera/object state all present.

The LingBot cam-only conversion is partial because the target MP4 still needs a
probe-confirmed writer fix. Therefore 10/50 generation remains disallowed until
the user explicitly approves 10-sample GPU0 use or a GPU6/7 TDW display is
available.
## 2026-06-04 TDW v2 Staging Update

Current generated-v2 status:

- `warmup_mild` 1-sample generation: passed.
- HDF5 validation: passed.
- LingBot cam-only conversion: passed.
- `target.mp4` probe: passed.
- 10-sample smoke: not run; requires explicit user approval if using GPU0-bound `DISPLAY=:8`.
- 50/200/1k generation: not allowed yet.

The accepted 1-sample is suitable for warmup inspection, but it is not enough for training or dataset-scale decisions. The next data action must be either:

1. configure a TDW display on GPU6/7 and run 10-sample smoke there; or
2. get explicit user approval to use GPU0-bound `DISPLAY=:8` for exactly 10 `warmup_mild` samples.

No full generation should start before 10-sample and 50-sample staged validation.

## 2026-06-04 10-Sample Warmup Mild Result

The approved GPU0-bound `DISPLAY=:8` 10-sample `warmup_mild` smoke completed successfully:

| Stage | Status |
|---|---|
| 1 sample | passed |
| 10 sample | passed |
| 50 sample | not run; approval required |
| 200 / 1k+ | not allowed |

10-sample metrics:

- generated HDF5 count: 10;
- validation ok: 10;
- rejected: 0;
- suitable_for_warmup: 10;
- target_visible_ratio: 1.0 for all;
- max invisible frames: 0;
- converted LingBot cam-only videos: 10;
- target.mp4 probe passed: 10.

Before 50-sample, resolve or explicitly accept the template coverage issue: this 10-sample run generated only `drop` scenes.

## 2026-06-03 Template Coverage Fix Status

The template coverage issue has been fixed at the wrapper/plan level:

- exact template counts are now supported;
- manifest-driven execution forces each planned row's template;
- dry-run plan distribution is `drop:3`, `collision:3`, `roll:2`, `containment:2`;
- stress/reobserve camera variant count remains zero.

Actual template-diverse 10-sample generation is still pending because it requires the current GPU0-bound TDW display `:8`. The current turn did not include a new GPU0 approval for this actual run.

Large-scale generation readiness:

| Scale | Status |
|---|---|
| template-diverse 10 | pending approval |
| 50 | no-go until template-diverse 10 passes |
| 200 | no-go |
| 1k+ | no-go |

Next required user decision: approve GPU0 `DISPLAY=:8` for exactly one template-diverse 10-sample smoke, or configure TDW on GPU6/7.

## 2026-06-04 Template-Diverse Actual Attempt

The approved GPU0 template-diverse 10-sample attempt did not pass:

- planned: `drop:3`, `collision:3`, `roll:2`, `containment:2`;
- actual command results: `drop` returned 0 for three commands, non-drop templates failed before generation;
- validation accepted: 0/10;
- conversion: skipped.

The code has been updated so drop-specific args are only passed to `drop`. However, the approval covered exactly one 10-sample attempt, so no rerun was started.

Large-scale generation status:

| Scale | Status |
|---|---|
| fixed template-diverse 10 | pending fresh approval |
| 50 | no-go |
| 200 | no-go |
| 1k+ | no-go |

## 2026-06-04 Non-Drop Template Retry Update

The non-drop retry narrowed the TDW blocker:

| Check | Result |
|---|---|
| non-drop command dry-run | passed; no drop-only args on non-drop templates |
| non-drop actual command returns | 3/3 returned 0 |
| non-drop HDF5 validation | 0/3, no HDF5 written |
| exact blocker | missing upstream `--run 1` |
| wrapper status | fixed to pass `--run 1` |
| template-diverse 10 retry | skipped pending fresh approval |

Large-scale generation remains blocked. The next staged generation step is not 50; it is a rerun of the fixed non-drop 3-sample smoke. Only after that and a template-diverse 10-sample retry pass should 50-sample validation be considered.

## 2026-06-04 Non-Drop `--run 1` Retry Result

The fixed non-drop smoke was rerun and still did not pass:

| Stage | Status |
|---|---|
| non-drop dry-run with `--run 1` | passed |
| collision actual | return 0, no HDF5 |
| roll actual | return 0, no HDF5 |
| containment actual | return 0, no HDF5 |
| template-diverse 10 | skipped |
| 50 | no-go |

This blocks any larger staged generation. The next data engineering task is to determine which upstream non-drop arguments or stimulus/template settings are required to make `collision`, `roll`, and `containment` write HDF5. Do not expand to 50/200/1k until this is solved and a template-diverse 10-sample validation passes.

## 2026-06-04 Non-Drop Output Path Fix and 10-Sample Pass

The non-drop HDF5 blocker is solved. Root cause was relative `--dir` path resolution from the upstream Physion workspace. The wrapper now passes absolute output directories.

Current staged status:

| Stage | Status |
|---|---|
| non-drop 3-sample | passed, 3/3 |
| template-diverse 10 | passed, 10/10 |
| LingBot cam-only conversion | passed, 10/10 |
| 50 validation | not run; approval required |
| 200 pilot | no-go |
| 1k+ full generation | no-go |

Template-diverse 10 distribution:

- drop: 3
- collision: 3
- roll: 2
- containment: 2

Next allowed data step is a user-approved 50-sample validation on `DISPLAY=:8` or after configuring a GPU6/7 TDW display. Do not run 200/1k+ without separate staged validation and explicit approval.

## Template-Diverse 50-Sample Validation Result

The staged TDW / Physion-style generation plan has now passed the 50-sample validation gate under explicit user approval for GPU0-bound `DISPLAY=:8`.

| Stage | Status |
|---|---|
| 1 sample | passed |
| drop-only 10 | passed, but not sufficient for template coverage |
| non-drop 3 | passed |
| template-diverse 10 | passed |
| template-diverse 50 | passed |
| 200 pilot | approval required |
| 1k+ | not allowed |

50-sample metrics:

- planned distribution: `drop:15`, `collision:15`, `roll:10`, `containment:10`;
- generated HDF5: 50;
- validation OK: 50;
- rejected: 0;
- suitable_for_warmup: 50;
- target_visible_ratio: 1.0 for every sample;
- max invisible frames: 0 for every sample;
- LingBot cam-only conversion: 50/50;
- `target.mp4` probe: 50/50;
- `use_action=false`: 50/50;
- dummy action norm: 0.0 for every sample.

Storage observed for the 50-sample gate:

- raw HDF5 directory: about 4.0 GB;
- converted LingBot cam-only directory: about 9.1 GB;
- contact sheets: about 6.4 MB.

The next allowed data step is not automatic. A 200-sample pilot requires user approval because it would again use GPU0-bound `DISPLAY=:8`, and the estimated storage is roughly 16 GB raw HDF5 plus 36 GB converted LingBot inputs. Full 1k+ generation remains blocked until staged validation and explicit approval.

## Visible-Motion Quality Gate Update

The template-diverse 50-sample stage is now reclassified:

- pipeline validation: passed;
- final warmup data quality: not passed;
- reason: camera motion is too weak to clearly test camera-conditioned world modeling.

Do not run 200 on the old `warmup_mild` profile. The next data stage should use:

`warmup_visible_motion`

Staged plan for visible-motion data:

1. 10-sample visible-motion smoke after GPU6/7 TDW display setup.
2. 50-sample visible-motion validation only after the 10-sample smoke is visually and quantitatively accepted.
3. 200-sample visible-motion pilot only after user approval.
4. 1k+ only after staged validation and explicit approval.

Current blocker:

No GPU6/7 TDW display is available. The only verified TDW display is GPU0-bound `DISPLAY=:8`; GPU0 is forbidden for the visible-motion run.
## 2026-06-05 Visible-Motion GPU0 Smoke Update

The old template-diverse 50-sample `warmup_mild` data is pipeline-valid but visually too static. Do not expand it directly to 200 / 1k as final warmup data.

The user approved GPU0-bound `DISPLAY=:8` for only a 1 -> 10 `warmup_visible_motion` smoke. Results:

- 1-sample visible-motion gate passed.
- 10 / 10 HDF5 generated.
- 10 / 10 passed HDF5/key/visibility validation.
- 5 / 10 passed `suitable_for_visible_motion`.
- 5 / 10 were converted to LingBot cam-only inputs.
- No 50 / 200 / 1k was run.

Do not request or run a 50-sample visible-motion validation until the profile is tuned:

- keep orbit 24/28 and strafe 0.50 candidates that show visible parallax;
- remove or strengthen dolly 0.25 because it remained too static;
- tune containment separately because orbit 24 produced too-large camera path under the current threshold;
- rerun a 10-sample smoke after tuning before asking for 50.

## 2026-06-05 Visible-Motion v2 Profile Update

`warmup_visible_motion_v2` was added to make camera motion template-aware:

- drop keeps orbit 24/28;
- collision uses strafe 0.50 and orbit 24, avoiding orbit 28;
- roll uses strafe/orbit, avoiding dolly;
- containment uses orbit 18/20 and strafe, avoiding orbit 24/28.

Local v2 plan dry-run passed:

- `drop:3`
- `collision:3`
- `roll:2`
- `containment:2`

Remote actual v2 generation did not launch because SSH to the TDW server repeatedly timed out/reset during code sync. Do not run 50 until v2 actual 10-sample validation passes the acceptance gate.

## 2026-06-06 Visible-Motion v2 Actual Gate Update

`warmup_visible_motion_v2` actual smoke has now passed.

Summary:

- generated HDF5: 10 / 10;
- validation OK: 10 / 10;
- suitable for visible motion: 10 / 10;
- converted to LingBot cam-only: 10 / 10;
- per-template accepted: drop 3, collision 3, roll 2, containment 2;
- no `too_static` or `too_extreme` samples.

The next staged data step is a 50-sample `warmup_visible_motion_v2` validation, but only after explicit user approval. The expected 50 distribution is `drop:15, collision:15, roll:10, containment:10`. Do not run 200 / 1k until the 50-sample stage is reviewed and approved.

## 2026-06-06 Visible-Motion v2 50-Sample Validation Update

The explicitly approved `warmup_visible_motion_v2` 50-sample validation has completed on GPU0-bound `DISPLAY=:8`.

Summary:

- planned distribution: `drop:15`, `collision:15`, `roll:10`, `containment:10`;
- generated HDF5: `50 / 50`;
- validation OK: `50 / 50`;
- suitable for visible motion: `50 / 50`;
- rejected: `0 / 50`;
- LingBot cam-only conversion: `50 / 50`;
- target visible ratio: `1.0` for all samples;
- camera path length min/avg/max: `0.5016 / 1.0778 / 1.4814`;
- background motion proxy min/avg/max: `0.0121 / 0.0211 / 0.0332`.

The raw HDF5 footprint for the 50-sample batch is about `4.31 GB`; the converted LingBot cam-only footprint is about `9.75 GB`.

Recommended next staged data step:

1. Ask the user to approve a 200-sample `warmup_visible_motion_v2` pilot.
2. Keep the same template-aware camera mapping unless manual video review finds a template-specific issue.
3. Do not run 1k+ until the 200-sample pilot is validated and explicitly approved.

Estimated 200-sample resource envelope based on this run:

- raw HDF5: about `17.2 GB`;
- converted LingBot cam-only inputs: about `39.0 GB`;
- runtime on GPU0-bound `DISPLAY=:8`: about `7 hours`;
- command must use the same `--profile warmup_visible_motion_v2` and a `drop:60,collision:60,roll:40,containment:40` plan.

No 200 / 1k generation is currently approved.

## 2026-06-06 Visible-Motion v3 Start0 Scene-Diverse Review

Manual review invalidated the previous v2 50-sample set as final warmup main data despite its numeric pass. The failure was qualitative: low perceived scene diversity, weak visible camera motion, and insufficiently clear frame-0 camera motion.

The new `warmup_visible_motion_v3_start0_scene_diverse` profile was tested on an explicitly approved 50-sample review set using `generated_v3`.

Summary:

- generated HDF5: `50 / 50`;
- validation OK: `50 / 50`;
- unique scene hashes: `50 / 50`;
- accepted for visible-motion v3: `28 / 50`;
- rejected: `22 / 50`;
- too static: `22 / 50`;
- delayed camera motion: `22 / 50`;
- too extreme: `0 / 50`;
- converted accepted LingBot cam-only samples: `28 / 28`.

Per-template accepted:

- drop: `11 / 15`;
- collision: `7 / 15`;
- roll: `4 / 10`;
- containment: `6 / 10`.

The run is not ready for 200. Scene diversity is fixed, but strafe variants at `0.55` and `0.65` fail the current early-motion and total-path gates. The next step is a smaller tuning smoke with stronger strafe, or an orbit-only review profile if camera-mode diversity is less important than acceptance. No 200 / 1k run is approved.

### Human-review update

The user manually reviewed the v3 50 videos and confirmed that all 50 are usable. The prior numeric no-go is now retained as diagnostic context only.

Operational status:

- human review accepted: `50 / 50`;
- all-50 LingBot cam-only conversion completed: `50 / 50`;
- `use_action=false` and dummy `action.npy` remain enforced;
- old `generated_v2` raw/conversion assets were deleted, reducing `generated_v2` from about `37G` to `254M`.

The next stage can be a 200-sample v3 pilot only after explicit user approval. The 200 pilot should continue using `generated_v3` and must not cascade into 1k+.

## 2026-06-07 Visible-Motion v3 200-Sample Pilot

The user requested the `warmup_visible_motion_v3_start0_scene_diverse` 200-sample pilot. The run completed on GPU0-bound `DISPLAY=:8`.

Summary:

- generated HDF5: `200 / 200`;
- validation OK: `200 / 200`;
- unique scene hashes: `200 / 200`;
- duplicate scene hashes: `0`;
- LingBot cam-only conversion: `200 / 200`;
- target.mp4 files: `200 / 200`;
- raw HDF5 footprint: about `17G`;
- converted cam-only footprint: about `37G`.

The pilot is ready for human review at:

`local_assets/reports/human_review/tdw_visible_motion_v3_start0_scene_diverse_200/video_gallery.html`

Next scale step, if human review passes, is 1k-scale generation only after explicit approval. Do not run 1k automatically.

## 2026-06-07 Visible-Motion v4 Stronger Start0 Smoke

The v3 200 pilot remains usable, but the user identified residual weak/slow camera motion. A stronger review smoke was run before any additional scale-up.

- profile: `warmup_visible_motion_v4_stronger_start0_review`;
- sample count: `16`;
- distribution: `drop:4, collision:4, roll:4, containment:4`;
- generated / validated / converted: `16 / 16 / 16`;
- suitable visible motion: `16 / 16`;
- too_static / too_extreme / delayed: `0 / 0 / 0`;
- camera path min/avg/max: `0.9017 / 1.4567 / 1.9758`;
- first-8-frame path min/avg/max: `0.0902 / 0.1457 / 0.1976`.

Recommended next scale step is a v4 50-sample review set only after human approval. Do not jump directly to 200 or 1k from this smoke.
## 2026-06-09 TDW v5 200 Warmup Gate

The user manually approved the `warmup_visible_motion_v5_aggressive_2x` 200-sample dataset as visually suitable. It is now the main warmup candidate, replacing earlier numerically-valid but visually weak warmup sets.

Current gate result:

- LingBot manifest: 200 samples.
- Integrity audit: 200 / 200 valid.
- Split: train 160, val 20, test 20.
- Dataloader smoke: passed.
- Forward-loss dry-run: only a placeholder no-model-load path passed; real LingBot-Fast model-load forward-loss remains a required pre-training gate.

No new TDW generation should run until the warmup data path is validated through a real model-load smoke and, if approved, a small warmup pilot. Do not run DPO, 200/1k expansion, reward calibration, or rollout as part of this gate.

## 2026-06-09 True Forward-Loss Gate Result

No new TDW data was generated.

The TDW v5 aggressive 2x 200 data remains the current human-approved warmup candidate. The real LingBot-Fast forward-loss gate now passes:

- manifest: `200`;
- split: `160 / 20 / 20`;
- dataloader smoke: passed;
- component load: passed;
- true forward-loss: passed across diagnostic high-noise, diagnostic low-noise, and random timestep bands.

This does not approve more TDW generation. The next data generation step is blocked until a warmup pilot demonstrates that the current v5 set is useful for camera-conditioned behavior. The next compute decision is a staged warmup pilot approval request, not a 200/1k TDW generation request.

## 2026-06-09 Stage A Warmup Pilot Result

The current TDW v5 aggressive 2x 200 dataset remains the main human-approved warmup candidate. A small Stage A LingBot-Fast warmup pilot was run against this dataset:

- GPU: GPU7;
- steps: 20;
- timestep band: diagnostic high-noise, timestep 799 / sigma 0.799;
- trainable scope: runtime `camera_control_lora_tiny`;
- trainable params: 40,960;
- train loss range: 0.030702 to 0.062314;
- val losses: 0.033537 and 0.034270;
- LoRA tensors changed: 4;
- sampled frozen base tensors changed: 0;
- no checkpoint, LoRA, optimizer state, rollout, reward calibration, TDW generation, or DPO was run.

The Stage A stability gate passed, but the first 20 split rows were all `collision + orbit_right_64`. The next compute gate should use a shuffled or template-balanced sampler before drawing conclusions about full dataset behavior. No additional TDW 200/1k generation is authorized by this result.

## 2026-06-09 Balanced Stage A Warmup Gate

No new TDW data was generated.

The TDW v5 aggressive 2x 200 dataset remains the active human-approved warmup candidate. The balanced Stage A high-noise warmup pilot now passes:

- steps: `60`;
- train template coverage: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- camera variants covered: 5;
- train loss finite, range `0.033201` to `0.067220`;
- val losses finite: `0.037449`, `0.046542`, `0.057670`;
- LoRA trainable params: `40,960`;
- LoRA tensors changed: `4`;
- sampled frozen base tensors changed: `0`;
- no NaN/Inf or OOM.

One adapter-only checkpoint was saved for later approved rollout inspection:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

This is not a data-generation approval. Do not run more TDW generation, Stage B, rollout, reward calibration, or DPO without explicit approval.
## 2026-06-10 TDW v5 Scale-Up Status

The v5 aggressive 2x 200 dataset remains the selected warmup dataset. It is human-approved and already has manifest, split, integrity, dataloader, true forward-loss, and balanced Stage A warmup gates.

No new TDW generation was run in this pass. TDW generation still requires a confirmed Xorg display. GPU4-7 are acceptable for PyTorch work, but do not by themselves provide TDW/Unity display binding. A separate approval is required for GPU0 `DISPLAY=:8` TDW generation or for setting up a GPU4-7 display.

Recommended order:

1. Run a bounded base-vs-Stage-A-adapter rollout smoke.
2. Score reward confidence on the rollout videos.
3. Build reward pairs only if confidence and margin pass.
4. Only then decide whether to expand TDW data beyond 200.

## 2026-06-10 Rollout Smoke Status

The bounded 4-condition base-vs-Stage-A-adapter rollout smoke is complete:

- drop / collision / roll / containment each have one condition;
- base videos: 4/4;
- Stage A adapter videos: 4/4;
- video probe: 12/12 across GT/base/adapter;
- human review gallery: `local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`.

No new TDW data was generated. No reward scoring, pair construction, DPO, VideoGPA `03_train`, Stage1, or training was run.

The next scale-up decision is not more TDW generation yet. First inspect the 4-condition gallery, then approve reward scoring on these videos or a 12-condition rollout.
