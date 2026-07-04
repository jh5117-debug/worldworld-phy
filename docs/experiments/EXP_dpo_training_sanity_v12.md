# EXP: DPO Training Sanity v12

## Current Status

The repaired DPO Pair Factory v11 ready500 data asset is canonical and ready for tiny training sanity:

- Canonical manifest: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Train/val/test/top50 repaired splits: 400 / 50 / 50 / 50.
- The old ready500 manifest is deprecated because three too-subtle pairs were removed and replaced.
- LPIPS real smoke is available.
- VBench real scoring smoke is available for `temporal_flickering` only.
- FVD real video-FVD smoke is available using a local TorchScript I3D backend, with tiny-smoke caveat.
- Previous DPO diagnostics showed winner-only instability and likely loser-dominant/no-signal behavior.

This experiment is tiny DPO training sanity only. It is not large-scale DPO.

## Problem

DPO can appear to improve preference margins by pushing losers worse while leaving winners unchanged or worse. That failure mode is not acceptable. Additional risks:

- camera-only LoRA may be too narrow;
- broader LoRA can destabilize video quality;
- vanilla sigmoid DPO can remain near `0.693` with no useful signal;
- synthetic controlled pairs dominate repaired ready500;
- metrics can disagree with visual quality;
- checkpoint loss alone is not evidence of success.

## Hypothesis

A tiny guarded objective over repaired ready500 subsets can become safer if:

- LoRA scope is selected by winner-anchor and visual/metric checks, not guessed;
- loser loss is gated by winner improvement;
- winner-anchor is explicit;
- pair weights reflect reward/severity/source;
- local time/region masks are used for controlled synthetic pairs when metadata exists;
- every checkpoint is evaluated with real videos, metrics, and Codex visual audit.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`

## Planned Subsets

- `S0_scope_probe_16`: LoRA scope winner-anchor probe.
- `S1_tiny_dpo_32`: guarded tiny DPO.
- `S2_small_dpo_64`: only if S1 is healthy.
- `S3_dpo_128_optional`: not run unless explicitly safe/authorized.
- `val_energy_16`: energy validation.
- `val_video_16`: checkpoint video evaluation.

## LoRA Scope Candidates

- `L0_camera_r4`: camera conditioning only, rank 4.
- `L1_camera_r8`: camera conditioning only, rank 8.
- `L2_camera_temporal_r4`: camera conditioning plus limited temporal/self-attention Q/K/V/O, max four blocks.
- `L3_camera_cross_r4`: camera conditioning plus limited cross-attention Q/K/V/O, max four blocks.
- `L4_adaln_camera_mod_r4`: camera / pose-conditioned AdaLN or modulation modules if present.

Forbidden scopes: broad-LoRA, FFN, all-block self/cross, full DiT, patch embedding, output head, VAE/T5 training.

## Objective

Primary objective candidate: `Guarded-SDPO-Anchor`.

Signals:

- `winner_improvement = E_ref_winner - E_policy_winner`
- `loser_degradation = E_policy_loser - E_ref_loser`
- `winner_contribution_ratio = positive(winner_improvement) / (positive(winner_improvement) + positive(loser_degradation) + eps)`

Loser branch starts disabled:

- `lambda_loser = 0` initially.
- Increase only after positive rolling winner improvement for three eval windows.
- Reset to zero if winner improvement is nonpositive or winner contribution ratio is below 0.30.

Fallback candidate: `Linear-DPO-Anchor`, only if guarded sigmoid runtime passes but shows no useful signal.

## Metrics

Every tiny DPO checkpoint must be checked with:

- PSNR;
- SSIM;
- LPIPS;
- FVD when sample count supports it, otherwise `FVD_SMOKE_ONLY`;
- VBench `temporal_flickering` at minimum;
- PhysGeo diagnostics;
- Codex visual audit on contact sheets.

## Success Gate

A tiny DPO run can pass only if all hold:

- no OOM / NaN / SIGFPE;
- grad nonzero;
- update norm positive;
- mean and final post-update winner improvement positive;
- winner contribution ratio at least 0.30;
- loser degradation is not the only margin source;
- PSNR/SSIM/LPIPS/FVD/VBench/PhysGeo do not show collapse beyond thresholds;
- Codex visual audit says checkpoint videos are not worse than step0/original;
- no freeze cheating, hallucination increase, or visual collapse;
- checkpoint video evaluation is complete.

## Failure Gate

Mark failed or blocked if any occur:

- winner improvement nonpositive;
- winner contribution ratio below 0.30;
- loser-only margin;
- video worse;
- freeze increases;
- hallucinated fragments increase;
- object identity worsens;
- metrics degrade materially;
- LoRA scope unstable;
- no checkpoint video audit.

Decision labels:

- `DPO_V12_PASS_TINY_ONLY`
- `DPO_V12_INCONCLUSIVE`
- `DPO_V12_FAILED_LOSER_DOMINANT`
- `DPO_V12_FAILED_WINNER_WORSE`
- `DPO_V12_FAILED_VISUAL_DEGRADATION`
- `DPO_V12_FAILED_NO_SIGNAL`
- `DPO_V12_RUNTIME_BLOCKED`
- `DPO_V12_SCOPE_BLOCKED`

No result in v12 permits large-scale DPO.

## Output Paths

- `reports/dpo_training_sanity_v12/`
- `manifests/dpo_v12_subsets/`
- `docs/dpo_training_sanity_v12_report.md`
- `docs/lora_scope_dpo_v12_decision.md`
- `reports/dpo_training_sanity_v12/self_review.md`

Training artifacts, videos, and contact sheet images remain local/untracked under `local_assets/` or report image folders and must not be pushed.

## What Is Not Run

- no large DPO;
- no StageB;
- no GRPO;
- no full-data StageA;
- no broad-LoRA;
- no checkpoint deletion;
- no MP4/JPG/PNG/checkpoint/weight push.
## Verification

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Pytest: unavailable in `/usr/bin/python3` (`No module named pytest`); no pytest PASS is claimed.
