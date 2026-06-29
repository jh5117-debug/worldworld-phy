# DPO Energy Audit and Training Recommendation

## Current Protocol v3 Status (2026-06-29 15:38:49)

- Metrics backend v2: PSNR/SSIM/LPIPS PASS; FVD/VBench BLOCKED_BY_ENV with attempted fixes recorded.
- LocalDPO spatial mask v2: PASS, 34/34 Type A pairs have usable spatial+time masks.
- Protocol v3: 34 valid Type A pairs, 0 Type B, 0 Type C.
- Candidate generator v2: waiting for GPU capacity; current GPUs are occupied by unrelated workloads.
- DPO smoke v3: not run yet because GPU capacity is unavailable; no scale DPO.



## Current DPO Protocol v2 Status (2026-06-29 14:18:28)

- Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Valid v2 pairs: 34 total, 34 Type A, 0 Type B, 0 Type C.
- Type B rollout losers are currently blocked by blur/sharpness gates; do not use them for DPO.
- Metrics backend: PSNR/SSIM/LPIPS pass; FVD and VBench are BLOCKED_BY_ENV.
- DPO engineering run-through: PASS_ENGINEERING_ONLY on 8 Type A pairs for 10 steps with checkpoint video eval. Learning signal remains loser-dominant, so do not scale DPO.
- Explicitly not run: StageB, GRPO, full-data long StageA, large-scale DPO.


Date: 2026-06-28
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Result

Protocol v1 now has a full real LingBot-Fast flow-matching energy audit for all 66 V2V-5 pairs. This audit used prefix frames 0-4 as condition, future frames 5-80 as the scored segment, same timestep/noise for winner and loser, frozen reference mode, and no optimizer step.

- Pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- Full energy table: `reports/dpo_preference_protocol_v1/full_real_energy_audit.csv`
- Full energy JSONL: `reports/dpo_preference_protocol_v1/full_real_energy_audit.jsonl`
- DPO-ready selection: `reports/dpo_preference_protocol_v1/dpo_ready_pair_selection.csv`
- DPO-ready pairs: `reports/dpo_preference_protocol_v1/dpo_ready_pairs.jsonl`
- LocalDPO-ready pairs: `reports/dpo_preference_protocol_v1/localdpo_ready_pairs.jsonl`

## Counts

- Total pairs audited with real energy: 66 / 66
- Failed energy rows: 0
- DPO-ready pairs selected: 50
- LocalDPO-ready pairs selected: 34
- Type A local corruption: 50 total, 34 selected
- Type B GT vs medium-hard rollout: 16 total, 16 selected
- Type C teacher/self rollout: 0

## Energy Margins

Type A local corruption:

- Delta_ref mean: 0.010276
- Delta_ref median: 0.009849
- Delta_ref min / max: -0.024275 / 0.028059
- Positive Delta_ref: 46 / 50
- Selected: 34 / 50

Type B GT vs medium-hard rollout:

- Delta_ref mean: 0.069783
- Delta_ref median: 0.075306
- Delta_ref min / max: 0.014672 / 0.117087
- Positive Delta_ref: 16 / 16
- Selected: 16 / 16

## Recommendation

Standard energy-DPO is now technically unblocked for a tiny probe, but should not be scaled yet. The first probe should use a small, auditable subset: all 16 Type B pairs plus the highest-energy-margin Type A pairs to reach 20-32 pairs. This gives a stronger energy signal while keeping anchored clean-GT winners.

SDPO-style safeguards are recommended for any probe beyond the smallest overfit test. The previous DPO probe degraded generated videos despite finite loss, so training must track winner_improvement, loser_degradation, and winner contribution to the margin. If the margin mostly comes from pushing losers worse, stop.

Linear-DPO-style objectives are recommended as the fallback for Type A local corruption pairs, because many Type A margins are modest and 11 pairs were rejected for weak/negative real-energy margin. If sigmoid DPO saturates or gives weak winner improvement, use linear utility or a non-saturating objective with an EMA reference.

LocalDPO-style region-aware DPO is promising for the 34 LocalDPO-ready Type A pairs. These pairs have affected region/time metadata and should be used with a future-only, region-aware loss/reward mask rather than a global video loss alone.

## Next Training Order

1. Energy-only sanity on selected 20 pairs: no optimizer, confirm deterministic margins.
2. One-pair and five-pair overfit probe with standard DPO, max 5-20 steps.
3. If winner_improvement is weak or loser_degradation dominates, switch to SDPO/Linear-DPO before scaling.
4. For LocalDPO-style training, start from the 34 Type A LocalDPO-ready pairs and use affected-region masks.

## Safety

No DPO training, StageB, GRPO, rollout, checkpoint mutation, or model update was run in this audit.


## 2026-06-28 DPO Objective Ablation S0

- S0_sanity_8 and S_localdpo_16 completed with real LingBot-Fast V2V-5 energy.
- Runtime/BF16 path was stable for Standard, SDPO-style, Linear-DPO-style, and LocalDPO-style diagnostics.
- Research signal failed: losses stayed near 0.693, Standard/Linear/LocalDPO showed winner-worse or loser-only behavior, and SDPO-style was only borderline at final step but failed mean winner-preservation gate.
- S1_probe_20 was not launched.
- No StageB, GRPO, large-scale DPO, or full-data StageA was run.
- Report: docs/dpo_objective_ablation_report.md