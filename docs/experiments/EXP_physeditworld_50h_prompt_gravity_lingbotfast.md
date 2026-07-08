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

