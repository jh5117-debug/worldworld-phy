# EXP PhysEditWorld 50h Prompt-Gravity LingBot-Fast

## Current Status

- LingBot-Fast is a large 14B-class video/world model backend in the project context.
- Previous DPO work partially repaired scalar objective diagnostics, but true rollout video quality remains unstable.
- Old ready500 preference data can support controlled tiny DPO diagnostics, but it does not solve PhysEditWorld gravity-editable training.
- The active line now shifts to PhysEditWorld matched replay: action trace, camera trajectory, intrinsics, and explicit gravity labels.
- H20 may be reclaimed, so required code, environment, weights, and data must be protected through migration manifests and PAI/NAS preparation.
- Only physical GPU4-7 may be used by this line. GPU0-3 are forbidden.

## Problem

- Ordinary SFT can damage LingBot-Fast generation quality if run without tight gates.
- Without support warm-up, LingBot-Fast may be too far from the PhysEditWorld action/camera/gravity distribution for meaningful anchored DPO.
- Pure self-rollout DPO is unsafe when the rollout pool is poor, because it may select only relatively less-bad winners.
- Prompt-only gravity comprehension is unknown and must be measured before adding architectural conditioning.
- Training must be gate-by-gate with checkpoint videos, metrics, and Codex visual audit.

## Hypothesis

- A PhysEditWorld 50h prompt-only gravity warm-up can move LingBot-Fast toward the gravity/action/camera-conditioned distribution while preserving the base architecture.
- Matched replay supervision with action + camera + gravity is cleaner than old passive camera-only data for this objective.
- Prompt-only gravity is the correct first baseline because it matches the paper-style conditioning and avoids adding an unvalidated gravity MLP or embedding.
- Anchored DPO should follow warm-up and visual/metric gates rather than start from poor self-rollouts.

## Inputs

- PhysEditWorld selected 50h.
- Image or prefix video.
- Text prompt with gravity token.
- Action trace.
- Camera trajectory.
- Intrinsics.
- Target video.
- Gravity label/value.
- Replay group metadata.

## Data Semantics

PhysEditWorld is not passive physics data. Each usable sample should preserve:

- same scene;
- same initial state;
- same action trace;
- same camera policy;
- gravity value/label;
- target video for that gravity.

`replay_group_id` groups samples that differ by gravity under matched replay conditions.

## Gravity Conditioning V0

First version is prompt-only:

```text
A first-person interactive world rollout.
The character follows the given action sequence and camera trajectory.
The scene is rendered under gravity: {gravity_value}g.
```

Do not leak future outcomes such as exact landing time, jump height, or fall speed. Do not add gravity MLP or gravity embedding in this version.

## Phase 0: H20 To PAI/NAS Migration Preparation

Outputs:

- `reports/migration/environment_no_builds.yml`
- `reports/migration/pip_freeze.txt`
- `reports/migration/required_weights_manifest.tsv`
- `reports/migration/required_data_manifest.tsv`
- `reports/migration/h20_to_pai_migration_plan.md`
- `scripts/migration/rsync_h20_to_pai_dryrun.sh`
- `scripts/migration/rsync_h20_to_pai_execute.sh`

Rules:

- Do not copy all of H20.
- Do not copy all `local_assets`.
- Do not copy old videos, contact sheets, or failed checkpoints by default.
- Execute script must require `MIGRATION_APPROVED=1`.

## Phase 1: PhysEditWorld 50h Data Audit

Build:

- `manifests/physeditworld_50h_all.jsonl`
- train/val/test and OOD split manifests.
- replay-group leakage report.
- gravity/scene/action distributions.

Gate:

- action trace exists;
- camera trajectory exists;
- intrinsics exists;
- gravity label exists;
- video decodable;
- prompt non-empty or generated;
- no duplicate sample id;
- no replay-group leakage.

If PhysEditWorld data is not found, stop training work and report `PHYS_EDIT_WORLD_DATA_NOT_FOUND` while preserving migration preparation.

## Phase 2: LingBot-Fast Input Conversion

Target sample layout:

```text
sample_dir/
  image.jpg or prefix.mp4
  target.mp4
  action.npy
  poses.npy
  intrinsics.npy
  prompt.txt
  gravity.json
  metadata.json
```

Conversion must be resumable, idempotent, atomic, and non-destructive to raw data. Frame indices must align video, action, camera, and intrinsics.

## Phase 3: Baseline Rollout

Evaluate Original LingBot-Fast and LingBot-Base if available on correct/wrong/default gravity prompts. Required outputs include generated manifest, gravity metrics, contact sheets, and Codex visual audit.

If the baseline ignores gravity, mark `PROMPT_ONLY_GRAVITY_BASELINE_WEAK`, but warm-up may still proceed through the first gate.

## Phase 4: Support Warm-Up

- Model: LingBot-Fast.
- Gravity: prompt-only.
- LoRA: rank32 first.
- Trainable: attention LoRA, camera/action condition projection LoRA if present, selected temporal/self-attention blocks.
- Frozen: VAE, text encoder, FFN, output head, most DiT backbone.
- BF16/mixed-safe with VAE FP32 and camera/action/intrinsics FP32.
- Gate steps: 5-step preflight, then 500/1000/2000 checkpoint gates.
- Use GPU4-7 only.

Stop on OOM, NaN, SIGFPE, forbidden GPU, or checkpoint video degradation.

## Phase 5: Warm-Up Checkpoint Evaluation

For step0/500/1000/2000, generate true rollouts and evaluate:

- Gravity Ordering;
- Airtime Error;
- Fall Speed Error;
- Contact Timing Error;
- Action Following;
- Camera Following;
- Freeze Rate;
- Visual Quality;
- VBench/LPIPS/FVD/DINO/V-JEPA where available.

Codex visual audit is mandatory. Best checkpoint is selected by video + metric evidence, not by final loss alone.

## Phase 6: Anchored DPO Pair Construction

Only after warm-up gate passes. Pair types:

- Type A: correct-gravity GT > warm-up bad rollout.
- Type B: correct-gravity GT > corrupted GT / wrong gravity / freeze / timing/camera mismatch.
- Type C: teacher/base better rollout > Fast bad rollout.
- Type D: high-score Fast rollout > low-score Fast rollout, only if winner quality passes.

Gate: at least 100 reviewed DPO-ready pairs for tiny anchored DPO.

## Phase 7: Tiny Anchored DPO Probe

Only after pair gate. Use 100 pairs and 50-200 steps. No scale in this round. Stop on winner failure, loser dominance, no-signal, video degradation, gravity regression, or forbidden GPU use.

## Phase 8: Later Ablation Plan

Write, but do not run, a follow-up plan comparing:

- A. PhysEditWorld 50h only.
- B. PhysEditWorld 50h + our physics 50h.

Compare gravity response, camera/background stability, object physics, reobserve, visual quality, and action/dummy-action semantic confusion.

## Success Gate

- Migration manifest complete.
- Environment export complete.
- Required weight/data manifests complete.
- 50h manifest valid.
- Replay-group-safe splits pass.
- Conversion smoke passes.
- Baseline rollout passes or has a documented gravity weakness.
- Warm-up checkpoint gates improve or preserve gravity/visual metrics.
- No freeze cheating.
- No GPU0-3 usage.

## Failure Gate

- SSH/repo blocked.
- Necessary data or weights missing after bounded search.
- Gravity labels missing.
- Action/camera misalignment.
- Replay group leakage.
- Warm-up videos degrade.
- Prompt-only gravity is not used.
- OOM, NaN, SIGFPE.
- Forbidden GPU use.
- Accidental large DPO.

## What Is Not Run

- No large DPO.
- No train400.
- No StageB.
- No GRPO.
- No full-data long StageA.
- No broad-LoRA.
- No data/checkpoint/weight deletion.
- No `local_assets` push.

## Execution Update: Phase 1 Data Audit (2026-07-08T18:05:23 CST)

The Phase 1 bounded audit did not find strict PhysEditWorld 50h samples in the current H20-visible paths. This blocks Phase 2+ until the actual PhysEditWorld selected 50h root is mounted or provided.

- Decision: `PHYS_EDIT_WORLD_DATA_NOT_FOUND`.
- Candidates inspected: 132.
- Strict OK samples: 0.
- Empty manifests were written intentionally to make downstream gates explicit.
- No GPU was used.
- No training was run.

## Execution Update: Root Search And Phase 2 Tooling (2026-07-08T18:29:06 CST)

- Root search decision: `PHYS_EDIT_WORLD_ROOT_NOT_VISIBLE`.
- Conversion tooling decision: `CONVERSION_TOOL_READY_DATA_BLOCKED`.
- Prompt-only gravity conversion is implemented, but no real samples are converted because the strict 50h manifest is empty.
- Phase 3+ remains blocked until the real PhysEditWorld selected 50h root is mounted or provided.


## Execution Update: Phase 3/4 Readiness (2026-07-08T18:44:19 CST)

- Phase 3 baseline rollout wrapper is implemented but correctly blocks on empty manifest with `BASELINE_BLOCKED_EMPTY_MANIFEST`.
- Phase 4 rank32 warm-up config is prepared for prompt-only gravity and GPU4-7 only.
- Gravity metric smoke passes on synthetic scalar rows.
- Direct Phase 3/4 smoke passes; pytest is unavailable in the active H20 shell.
- True baseline rollout and support warm-up are not run because the selected PhysEditWorld 50h root remains unavailable and the converted train manifest has 0 rows.
- No scale, no StageB, no GRPO, no broad-LoRA, no DPO, and no checkpoint/video push.


## PAI / Data Readiness Preflight Update (2026-07-08T19:00:08 CST)

Decision: `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`.

A CPU/IO-only readiness checker was added and run:

- Tool: `cam_physgeo/data/physeditworld_readiness.py`.
- Wrapper: `scripts/migration/check_physeditworld_pai_readiness.sh`.
- Checklist: `docs/physeditworld_50h_data_unblock_checklist.md`.
- CSV: `reports/migration/physeditworld_pai_readiness.csv`.
- JSON: `reports/migration/physeditworld_pai_readiness.json`.
- Summary: `reports/migration/physeditworld_pai_readiness_summary.md`.

Current blockers are explicit and machine-readable:

- NAS target `/mnt/workspace/hj/nas_hj` is not mounted/visible.
- No external-looking selected PhysEditWorld 50h root candidate is visible.
- `manifests/physeditworld_50h_all.jsonl`, train manifest, and LingBot train manifest all have 0 rows.

Test status: compileall PASS, direct readiness smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, warm-up, pair construction, or DPO was run.


## Phase 4/6 Gate Scaffold Update (2026-07-08T19:06:16 CST)

Decision: `WARMUP_BLOCKED_EMPTY_MANIFEST` and `PAIR_BUILDER_BLOCKED_WARMUP_GATE`.

New safety-gated entry points were added:

- Warm-up gate: `cam_physgeo/training/train_physeditworld_warmup.py`.
- Anchored pair gate: `cam_physgeo/dpo/physeditworld_pair_builder.py`.
- Tests: `tests/test_physeditworld_warmup_trainer.py`, `tests/test_physeditworld_pair_builder.py`.

Smoke evidence:

- Warm-up preflight report: `reports/physeditworld_50h_warmup_rank32/preflight.csv`.
- Warm-up preflight summary: `reports/physeditworld_50h_warmup_rank32/preflight_summary.md`.
- Pair gate audit: `reports/physeditworld_dpo_pairs_anchored_v0/pair_audit.csv`.
- Pair gate summary: `reports/physeditworld_dpo_pairs_anchored_v0/pair_summary.md`.

The warm-up command was invoked with `CUDA_VISIBLE_DEVICES=4`, which passes the GPU4-7 policy, but it correctly refused to train because `manifests/physeditworld_50h_lingbot_train.jsonl` has 0 rows. The pair builder correctly emitted an empty anchored-pair manifest because no warm-up checkpoint has passed video/metric/Codex audit.

Test status: compileall PASS, direct Phase 4/6 smoke PASS, pytest unavailable; no pytest PASS is claimed. No rollout, no training, no pair admission, and no DPO was run.


## Phase 5/7 Gate Scaffold Update (2026-07-08T19:13:39 CST)

Decision: `CHECKPOINT_EVAL_BLOCKED_EVAL_MANIFEST_MISSING` and `TINY_DPO_BLOCKED_INSUFFICIENT_PAIRS`.

New safety-gated entry points were added:

- Checkpoint eval gate: `cam_physgeo/eval/physeditworld_checkpoint_eval.py`.
- Tiny anchored DPO gate: `cam_physgeo/dpo/physeditworld_tiny_dpo_probe.py`.
- Tests: `tests/test_physeditworld_checkpoint_eval.py`, `tests/test_physeditworld_tiny_dpo_probe.py`.

Smoke evidence:

- Checkpoint eval summary: `reports/physeditworld_50h_warmup_rank32/checkpoint_eval_gate_summary.md`.
- Gravity metrics placeholder: `reports/physeditworld_50h_warmup_rank32/gravity_metrics.csv`.
- Video audit placeholder: `reports/physeditworld_50h_warmup_rank32/video_audit.csv`.
- Tiny DPO gate summary: `reports/physeditworld_tiny_dpo_v0/tiny_dpo_gate_summary.md`.
- Tiny DPO decision: `reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json`.

The checkpoint eval gate was invoked with `CUDA_VISIBLE_DEVICES=4`, which passes the GPU4-7 policy, but it correctly refused to evaluate because `manifests/physeditworld_50h_lingbot_val.jsonl` is missing. The tiny DPO gate also used `CUDA_VISIBLE_DEVICES=4` and correctly refused to train because the anchored pair manifest has 0 rows, below the 100-pair gate.

Test status: compileall PASS, direct Phase 5/7 smoke PASS, pytest unavailable; no pytest PASS is claimed. No rollout, no metrics scoring, no visual audit, no training, and no DPO was run.


## Pipeline Gate Orchestrator Update (2026-07-08T19:18:47 CST)

Decision: `PIPELINE_BLOCKED_AT_READINESS`.

A safe phase-gate orchestrator was added:

- Orchestrator: `cam_physgeo/orchestration/physeditworld_pipeline_gate.py`.
- Launch script: `scripts/run_physeditworld_pipeline_gates.sh`.
- Test: `tests/test_physeditworld_pipeline_gate.py`.
- CSV: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.csv`.
- JSON: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json`.
- Summary: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md`.

The orchestrator reruns/reads readiness first and stops before baseline, warm-up, checkpoint eval, pair construction, or tiny DPO when prerequisites are blocked. Current stop point is readiness because NAS and the selected PhysEditWorld 50h root are not visible and the strict/LingBot manifests are empty.

Test status: compileall PASS, direct pipeline gate smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, metrics scoring, visual audit, training, or DPO was run.


## PAI Bootstrap And Requirement Matrix Update (2026-07-08T19:27:35 CST)

Decision: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`.

Added PAI recovery and requirement-audit artifacts:

- PAI bootstrap script: `scripts/migration/bootstrap_pai_physeditworld.sh`.
- Bootstrap doc: `docs/physeditworld_50h_pai_bootstrap.md`.
- Requirement matrix generator: `cam_physgeo/orchestration/physeditworld_requirement_matrix.py`.
- Test: `tests/test_physeditworld_requirement_matrix.py`.
- Matrix CSV/JSON/MD: `reports/physeditworld_50h/requirement_matrix.*`.

Current matrix: 19 requirements total, 11 PASS, 7 BLOCKED, 1 MISSING. The earliest blocker remains migration/data readiness: NAS and selected PhysEditWorld 50h root are not visible.

Test status: compileall PASS, direct requirement-matrix smoke PASS, pytest unavailable; no pytest PASS is claimed. No GPU, rollout, metrics scoring, visual audit, training, or DPO was run.


## Post-Mount Continuation Update (2026-07-08T19:34:47 CST)

Decision: `POST_MOUNT_BLOCKED_AT_ROOT_INPUT`.

Added a safe continuation entry point for the moment the selected PhysEditWorld 50h root becomes visible:

- Tool: `cam_physgeo/orchestration/physeditworld_post_mount.py`.
- Launch script: `scripts/continue_physeditworld_after_mount.sh`.
- Doc: `docs/physeditworld_50h_post_mount_continue.md`.
- Test: `tests/test_physeditworld_post_mount.py`.
- Status CSV/JSON/MD: `reports/physeditworld_50h/post_mount/post_mount_status.*` and `post_mount_summary.md`.

Usage after mount:

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h \
bash scripts/continue_physeditworld_after_mount.sh
```

With no root provided, the smoke correctly blocks at root input. The continuation does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, deletion, or large-file push.

Test status: compileall PASS, direct post-mount smoke PASS, pytest unavailable; no pytest PASS is claimed.

## Migration Asset Validation Update (2026-07-08T19:58:00 CST)

Decision: MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.

A read-only migration asset validator was added and run before any H20 to PAI/NAS copy:

- Tool: cam_physgeo/orchestration/migration_asset_validator.py.
- Wrapper: scripts/migration/validate_physeditworld_migration_assets.sh.
- Doc: docs/physeditworld_50h_migration_asset_validation.md.
- CSV: reports/migration/migration_asset_validation.csv.
- JSON: reports/migration/migration_asset_validation.json.
- Summary: reports/migration/migration_asset_validation_summary.md.

Validation evidence:

- Manifest rows checked: 800 total, 300 weights rows and 500 data rows.
- Present file bytes counted: 5.97 GB.
- Execute script guard: PASS; MIGRATION_APPROVED=1 is required.
- NAS target /mnt/workspace/hj/nas_hj: BLOCKED_MISSING.
- Safety: no files copied, no files deleted, no large directory recursive hashing, no local_assets payload.

This confirms migration execution is still blocked on the NAS mount/visibility, not on the validator itself. No GPU, rollout, warm-up, pair construction, or DPO was run.

## Requirement Matrix Asset-Validation Update (2026-07-08T20:06:00 CST)

Decision remains: PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS.

The requirement matrix now includes migration asset validation as an explicit Phase 0 gate:

- Requirement count: 20.
- Status counts: PASS=11, BLOCKED=8, MISSING=1.
- New Phase 0 row: migration asset validation = BLOCKED.
- Evidence: reports/migration/migration_asset_validation.json.
- Detail: decision=MIGRATION_ASSET_VALIDATION_NAS_BLOCKED.

This makes the current migration blocker sharper: both PAI/NAS data readiness and migration asset validation are blocked until /mnt/workspace/hj/nas_hj and the selected PhysEditWorld 50h root are visible. No training, rollout, metric scoring, pair construction, or DPO was run.

