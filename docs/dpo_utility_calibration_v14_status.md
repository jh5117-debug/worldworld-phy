# DPO Utility Calibration v14 Status

Updated: 2026-07-07 CST

## Current State

- Canonical repaired ready500 exists and remains the required data entry. The old `manifests/dpo_pair_factory_v11_ready_500.jsonl` is not used.
- v13b completed with `DPO_RECIPE_NOT_FOUND`.
- Best v13b training-signal candidate was `S07_linear_winner_detached`, but it failed checkpoint metric gate due VBench temporal_flickering worsening.
- S03/S06/S09 were winner-positive and non-loser-dominant, but DPO loss stayed near 0.693 and preference utility stayed near 1e-4.
- S10 camera+temporal LoRA produced 18 rows but final winner_improvement_post was negative.
- Current blocker is preference utility / gap scale, not pair count.

## v14 Goal

v14 will perform offline utility calibration, beta/lambda response analysis, and latent monitor audit before any new DPO search. The run must explain why utility is near 1e-4 and identify whether normalization, reduction mode, local mask, sigma-bin normalization, pair source, or beta scale is the main blocker.

## GPU Rule

Only H20 physical GPU4 and GPU5 are allowed for v14 energy, latent-monitor, eval, and training jobs. GPU0/1/2/3/6/7 are forbidden for this experiment.

## Scope

Allowed:
- offline energy / utility calibration;
- V-JEPA / VideoREPA / TRD monitor if local backend exists;
- up to 10 small calibrated DPO objective schemes, each <=200 steps;
- checkpoint video + metrics + Codex audit only for promising schemes.

Forbidden:
- train400;
- large DPO;
- S32/S64;
- StageA / StageB / GRPO;
- broad-LoRA;
- checkpoint/data/weight deletion;
- pushing videos/images/checkpoints/local_assets.

## Initial Decision

Proceed with v14 PRD, pair inventory, offline utility calibration, beta response sweep, latent monitor backend audit, and calibrated scheme design. Do not start large training.
