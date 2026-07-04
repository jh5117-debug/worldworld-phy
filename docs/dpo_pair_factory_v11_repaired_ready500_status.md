Current Status: STARTED

# DPO Pair Factory v11 Repaired Ready500 Status

Generated: 2026-07-04 11:46:48

## Current Facts

- Old ready500 manifest: `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- Old ready500 had 3 pairs rejected after loser audit due `too_subtle_metric`.
- Repaired ready500 manifest: `manifests/dpo_pair_factory_v11_ready_500_after_loser_audit_repaired.jsonl`
- Repaired manifest composition: 497 original pass pairs + 3 replacements.
- The repaired manifest is now intended to become the canonical training data entry.

## Metric Backend Status Before This Round

- LPIPS: PASS. Real LPIPS alex smoke already passed.
- VBench: package and CLI are available, but real scoring is still pending.
- FVD: still blocked. No valid local video-FVD/I3D backend was found; image FID must not be used as FVD.
- Environment caveat: VBench install added user-site `transformers==4.33.2`, while fastwam expects `transformers==4.49.0`.

## This Round

Only data freeze and metric backend verification are run:

1. Re-freeze repaired ready500 as canonical and regenerate repaired train/val/test/top subsets.
2. Run small real LPIPS metric smoke on repaired pairs.
3. Run VBench real scoring smoke if possible, otherwise report exact blocker.
4. Audit FVD backend honestly; do not use image FID as FVD.

No training, DPO, SDPO, Linear-DPO, winner-anchor, StageA, StageB, or GRPO is run.
