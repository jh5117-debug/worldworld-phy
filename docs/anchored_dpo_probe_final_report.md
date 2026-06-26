# Anchored DPO Probe Status (2026-06-27 04:43:25)

Current decision: tiny DPO probe is not launched yet.

Completed prerequisite:
- Rebuilt anchored DPO pairs as true V2V-5 prefix pairs.
- Verified 50/50 pairs: prefix_len=5, prediction_start_frame=5, prefix 5 frames, future 76 frames.

New prerequisite in progress:
- Real LingBot-Fast energy backend is now implemented for preflight.
- DPO probe may proceed only if BF16 preflight passes and energy diagnostics are finite with nonzero LoRA gradients.

No large-scale DPO, StageB, GRPO, or full-data StageA was run in this update.


---

# Anchored DPO Probe Final Report

Updated: 2026-06-27 01:28:06

## Status

`DPO_PROBE_BLOCKED`

## What Completed

- Anchored pair manifest exists with `50` pairs.
- Energy-form DPO loss implemented.
- Diagnostic DPO preflight completed and passed.
- Same noise/timestep tests pass.
- Save/load for the diagnostic adapter state passes.

## What Did Not Complete

- Real LingBot-Fast DPO training did not run.
- DPO BF16 single/DDP preflight did not run on the real backend.
- DPO checkpoint rollout/video audit/metrics did not run.

## Blocker

LingBot-Fast rollout initialization is available in prior artifacts, but the anchored DPO energy path has not yet exposed a callable winner/loser flow-matching energy function with frozen reference.

## Decision

Do not scale DPO yet. The next step is to implement the real LingBot-Fast energy path, then run the requested single-GPU, DDP2, and DDP8 BF16 DPO preflights before any DPO probe training.


## Prefix-5 Pair Rebuild Status (2026-06-27 03:24:08)

- Old anchored pairs were I2V-1 / first-image conditioned, not V2V-5.
- New manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`.
- Pair count: `50`.
- Valid prefix5 pair count: `50`.
- Prefix clips use frames 0-4; winner/loser futures use frames 5-80.
- DPO loss/reward masks are `5..80`.
- Real DPO remains blocked until LingBot-Fast winner/loser energy backend and BF16 DDP preflight are available.
