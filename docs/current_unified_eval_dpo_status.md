# Current Unified Eval / DPO Status

<!-- DPO_FAILURE_DIAG_20260629_START -->
## Current Status: DPO Failure Root-Cause Diagnosis Completed (2026-06-29)

- S0_sanity_8 objective ablation failed the signal gate, so S1/S2 were not launched.
- Winner-only overfit on the strongest Type B pair did not robustly improve winner energy relative to the reference: mean winner improvement = -2.27876e-05, final = -4.29377e-05.
- Loser-only maximization was weak/non-monotonic: mean loser degradation = 1.04467e-04, final = -1.55047e-04.
- Gradient decomposition found mixed winner/loser alignment: mean cosine(g_w,g_l) = 0.065 and winner/loser grad norm ratio ranged from 0.417 to 10.228.
- Timestep/sigma sensitivity is currently blocked for low/mid bins because all requested bins map to actual sigma about 0.947 in the DPO backend.
- Beta/utility analysis shows `u = Delta_policy - Delta_ref` is effectively zero at initialization, so standard sigmoid DPO starts at the no-margin 0.693 point.
- LocalDPO metadata contains affected spatial masks for 34 / 34 local-corruption pairs, but the current LocalDPO objective only used affected-time masking; spatial-token masking remains TODO.
- Decision: do not proceed with standard DPO or scale DPO. Next probe should use an explicit winner-anchor objective plus conservative loser lambda, and only after spatial LocalDPO masks / sigma sampling are fixed.
- Report: `docs/dpo_failure_root_cause_report.md`.

Safety: no large DPO, no StageB, no GRPO, no full-data StageA, no checkpoint deletion, and no data/weight/video push.
<!-- DPO_FAILURE_DIAG_20260629_END -->


<!-- ENERGY_AUDIT_20260628_START -->
## Current Status: Full Real-Energy Audit Completed (2026-06-28)

- Protocol v1 pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Full real LingBot-Fast energy audit completed for 66 / 66 V2V-5 pairs.
- Real energy outputs: `reports/dpo_preference_protocol_v1/full_real_energy_audit.csv` and `.jsonl`.
- DPO-ready selection: 50 pairs total = 34 Type A local corruption + 16 Type B GT vs medium-hard rollout.
- LocalDPO-ready subset: 34 Type A pairs with affected region/time metadata and positive usable energy margin.
- Type B pairs have stronger real-energy margins (Delta_ref median 0.075306) than Type A local corruptions (Delta_ref median 0.009849), but Type A is better aligned with region-aware LocalDPO.
- Recommendation: tiny standard energy-DPO is unblocked only as a controlled probe; use SDPO-style winner-preserving monitoring and consider Linear-DPO for weak-margin Type A pairs.
- No DPO training, StageB, GRPO, full-data StageA, checkpoint deletion, or data/weight push was run for this audit.

<!-- ENERGY_AUDIT_20260628_END -->

Updated: 2026-06-28T00:20:04

## Current Protocol State

- DPO training: not running.
- New pair protocol: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Valid pairs: 66.
- Type A local corruption: 50.
- Type B medium-hard rollout: 16.
- Prior DPO probe remains failed for scale-up; this protocol is the data repair step.

## Decision

Pair protocol v1 is ready for review and selected-subset real-energy audit. It is not approval to launch DPO automatically.

---

# Current Unified Eval / DPO Status

Updated: 2026-06-27T07:14:17

## Current Status

- Prefix-aware V2V-5 pairs: READY (`manifests/anchored_dpo_probe_pairs_prefix5.jsonl`, 50/50 visual-audited valid prefix5 pairs).
- Real LingBot-Fast prefix5 DPO energy backend: READY for preflight.
- DPO BF16 runtime: **DPO_BF16_READY**.
- Tiny DPO probe: **BLOCKED** until a verified V2V-5 LingBot-Fast generation wrapper is implemented for checkpoint video evaluation.
- No large-scale DPO, StageB, GRPO, or full-data long StageA was run in this step.

## Latest BF16 Preflight Outputs

- Matrix: `reports/dpo_bf16_preflight/matrix.csv`
- Energy summary: `reports/dpo_bf16_preflight/energy_checks_summary.csv`
- Single: `reports/dpo_bf16_preflight/lingbot_fast_single_gpu7_20260627_053617/`
- DDP2: `reports/dpo_bf16_preflight/lingbot_fast_ddp2_gpu67_20260627_060736/`
- DDP8: `reports/dpo_bf16_preflight/lingbot_fast_ddp8_gpu01234567_20260627_063825/`

## Why Probe Is Not Started Yet

The DPO trainer can now compute real energy and update LoRA. However the probe specification requires real V2V-5 rollout videos for every checkpoint. The current inference wrapper is image-first and would be I2V, not V2V-5. Running it would invalidate the probe.


## 2026-06-28 DPO Objective Ablation S0

- S0_sanity_8 and S_localdpo_16 completed with real LingBot-Fast V2V-5 energy.
- Runtime/BF16 path was stable for Standard, SDPO-style, Linear-DPO-style, and LocalDPO-style diagnostics.
- Research signal failed: losses stayed near 0.693, Standard/Linear/LocalDPO showed winner-worse or loser-only behavior, and SDPO-style was only borderline at final step but failed mean winner-preservation gate.
- S1_probe_20 was not launched.
- No StageB, GRPO, large-scale DPO, or full-data StageA was run.
- Report: docs/dpo_objective_ablation_report.md

