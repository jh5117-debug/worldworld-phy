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
