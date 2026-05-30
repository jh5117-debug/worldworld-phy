# Reward On Fast Rollout Failure Analysis

## Original Failure

The original rollout reward ranked Fast above clean GT:

- Clean GT avg `R_total`: `0.5949`
- Fast rollout avg `R_total`: `0.8796`
- Clean > Fast win rate: `0.0`

This reward is not usable for DPO pair selection.

## Debug Run

Updated reward aggregation now reports per-component confidence and extra score variants:

- `R_total`
- `R_total_no_quality`
- `R_total_confidence_weighted`
- `R_geometry_only`
- `R_identity_only`
- `R_motion_only`
- `R_quality_only`
- `P_freeze`

Debug output:

```text
local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v2/
```

## Confidence-Weighted Result

- Clean GT avg confidence-weighted reward: `0.2173`
- Fast rollout avg confidence-weighted reward: `0.2256`
- Clean > Fast confidence-weighted win rate: `0.3333`

The confidence-weighted score is now low in absolute value because all critical geometry/identity/physics components are fallback/proxy. That fixes the earlier issue where fallback rewards could look high-confidence. It does not fully fix ranking: Fast still slightly exceeds clean on two of three samples.

## Why Fast Still Scores High

The main misleading term is still `R_phys` / motion proxy:

- `physion_movingcam_07abddf5748b`: clean minus Fast `R_phys = -0.3522`
- `physion_movingcam_13db379640ce`: clean minus Fast `R_phys = -0.3373`
- `physion_movingcam_1a0d32560b71`: clean minus Fast `R_phys = -0.1764`

Fast rollouts get motion-proxy credit that is not grounded in object state, ID masks, or physical event semantics.

`R_quality` is not the main cause:

- Quality deltas are small: `+0.0232`, `-0.0003`, `+0.0133` clean-minus-Fast.

Clean GT is also penalized by `P_freeze` in two samples:

- `07abdd...`: clean freeze penalty `0.5`, Fast `0.0`
- `1a0d...`: clean freeze penalty `0.25`, Fast `0.0`

This indicates the current frame-diff freeze proxy can misread low-motion clean physical clips as freeze.

## Metadata / Backend Issue

Clean samples expose depth, ID mask, camera pose, and intrinsics in metadata, but the current reward path still mostly uses frame-diff and proxy visual features rather than real depth/ID/flow features. Therefore clean GT metadata is present but underused.

Generated Fast rollouts lack reliable depth/ID/flow/feature backends. Their component confidence is low:

- Clean overall confidence: about `0.2853`
- Fast overall confidence: about `0.2559`

Both clean and Fast rows are marked `reward_provisional=true`.

## Conclusion

Gate D remains failed / not reliable. Confidence scaling now prevents fallback high-confidence claims, but the reward still cannot rank clean GT above Fast consistently. Next minimal action is to replace `R_phys` and `P_freeze` proxies with object-state/ID-mask/flow-aware implementations before using reward for pair selection.
