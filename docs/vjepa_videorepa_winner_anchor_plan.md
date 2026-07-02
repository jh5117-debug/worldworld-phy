Current Status Update (2026-07-02 21:58:17): V8G_MONITOR_FIRST_UPDATE

The explicit LingBot-Fast winner-energy path is still bottlenecked by integrated policy runtime/cache loading. V-JEPA / VideoREPA remains monitor-first and must not be integrated into training until the policy runtime/cache path is stable. No model download or training integration was performed.

Current Status:
MONITOR_FIRST_RUNTIME_BLOCKED

## 2026-07-02 v8f Update

Explicit winner-energy training is still blocked by runtime/cache plumbing before cache10. v8f narrowed the active blocker to CPU-side policy model construction / shard loading in `WanModelFast.from_pretrained`. V-JEPA / VideoREPA should remain monitor-first and must not be integrated into training until the policy runtime/cache path is stable. No model download and no training integration were performed.

Current Status:
MONITOR_PLAN_GPU_BLOCKED

## 2026-07-02 v8e Update

Explicit winner-energy anchor is still blocked before cache10. V-JEPA / VideoREPA remains monitor-first; do not integrate into training while runtime/cache preflight is unresolved. No model download was performed.

Current Status:
MONITOR_PLAN_CACHE10_BLOCKED

## 2026-07-02 v8d Update

Explicit winner-energy anchor is still blocked at reusable cache construction. V-JEPA / VideoREPA should remain monitor-first and should not be integrated into training before cache10 winner-anchor passes or a new winner-side signal path is validated. No model download was performed.

Current Status:
DESIGN_ONLY_NOT_INTEGRATED

## 2026-07-02 07:45 CST v8c Update

Explicit winner-energy anchor is memory-safe and positive on 1 reviewed pair with window49, but it is not yet scalable to 10 pairs because repeated VAE/T5 cache construction is too slow. V-JEPA / VideoREPA remains monitor-first only. Do not integrate it into training until the explicit energy winner-anchor path passes the 10-pair gate. Later objective remains: L = L_safe_DPO + lambda_E * L_winner_energy_anchor + lambda_J * L_VJEPA_TRD_winner.

Current Status:
DESIGN_ONLY_NOT_INTEGRATED

# V-JEPA / VideoREPA Winner Anchor Plan

Updated: 2026-07-01 23:59 CST

## Purpose

Tiny SDPO-anchor v7 was engineering-stable but did not preserve the winner at the final checkpoint. This document defines a latent winner-anchor monitor and later objective extension using local V-JEPA or VideoREPA features if they are already available locally. No model download or training integration is authorized by this document.

## Current Constraint

The current DPO energy objective can become loser-dominant. Before adding another loss term, v8 first checks sigma mapping and winner-anchor-only behavior. V-JEPA / VideoREPA is a monitor-first plan and should not be used to claim DPO success until its correlation with visual winner preservation is verified.

## Monitor Definition

For each checkpoint rollout and its GT winner:

1. Decode the same future frame window 5-80 for policy rollout and GT winner.
2. Sample a fixed temporal grid, for example 8 or 16 frames, keeping the same frame indices across checkpoints.
3. Resize and normalize according to the local V-JEPA / VideoREPA encoder requirement.
4. Extract latent tokens for the GT winner and policy rollout with the encoder in frozen eval mode.
5. Compute:
   - global cosine similarity between pooled winner and rollout features;
   - token-level temporal relation distance;
   - affected-region relation distance if masks are available;
   - background/outside relation distance to detect scene drift.

The first output should be a monitor CSV, not a training loss.

## Winner Latent Relation

Let `z_w[t, i]` be the frozen latent token for the GT winner at sampled time `t` and spatial/token index `i`; let `z_p[t, i]` be the policy rollout token. Define:

- pooled cosine: `mean_cos(pool(z_w), pool(z_p))`;
- temporal relation distance: pairwise relation mismatch across sampled times;
- token relation distance: local token neighborhood mismatch;
- optional mask-weighted distance if affected masks are available.

A lower relation distance and higher cosine should indicate better winner preservation, but this must be checked against Codex visual audit before use as an objective.

## Monitor CSV Fields

- checkpoint_step
- pair_id / condition_id
- rollout_video
- gt_winner_video
- encoder_backend = local_vjepa | local_videorepa | blocked
- sampled_frame_indices
- pooled_cosine
- temporal_relation_distance
- affected_relation_distance if masks exist
- outside_relation_distance
- visual_audit_status
- notes

## Later Objective Sketch

Only after monitor validation, a later objective may use:

`L = L_safe_DPO + lambda_E * L_winner_energy_anchor + lambda_J * L_VJEPA_TRD_winner`

where:

- `L_safe_DPO` is the conservative preference objective with loser lambda gated by winner improvement;
- `L_winner_energy_anchor = E_policy_winner`;
- `L_VJEPA_TRD_winner` is the latent relation distance between policy rollout and GT winner;
- `lambda_J` starts at a small value and is tuned only after monitor/visual alignment is known.

## Blocked / Not Run

- No V-JEPA or VideoREPA model download.
- No training integration in v8 unless objective A/B/C are blocked and the local encoder already exists.
- No latent objective is used for DPO-ready claims until it has visual-audit correlation.

## Next Check

Search local paths for existing V-JEPA / VideoREPA encoders and weights. If no local backend is present, mark `BLOCKED_BY_ENV_LOCAL_ENCODER_MISSING` and keep this as a future monitor plan.

## v8b Update

Current Status: DESIGN_ONLY_NOT_INTEGRATED

v8b did not authorize V-JEPA/VideoREPA training integration. Sigma mapping is now bounded and separated, but winner-anchor-only failed by OOM after one completed step with winner_improvement = 0.0. The latent winner anchor should remain a monitor-first plan: use it to measure whether future memory-safe winner-anchor runs preserve GT winner structure before adding `lambda_J * L_VJEPA_TRD_winner` to training. No large model download was performed.


## v8h Update - 2026-07-03T06:46:04

Policy runtime safe loader now reaches runtime-ready on H20 physical GPU7. The first-row cache smoke then blocks after `after_policy_load` and before `after_runtime_ready`, localizing the next blocker to `ensure_runtime_ready` / runtime component initialization. DPO remains not ready; no DPO/SDPO/Linear-DPO was run.
