# DPO Preference Protocol v3 Report

Current Status: MIXED_TYPEA_READY_TYPEB_FAILED_CANDIDATE_GENERATOR

Protocol v3 remains TypeA-only after candidate-generator v2 audited existing true V2V-5 overnight small-LoRA rollouts. TypeB rollout losers remain blocked because no candidate was both clear enough and medium-hard enough under the stricter quality/sharpness gate.

- Manifest: `manifests/dpo_preference_protocol_v3_pairs.jsonl`
- Total valid pairs: 34
- Type A local corruption: 34
- Type B rollout loser: 0
- Type C: 0
- Candidate-generator v2 report: `docs/candidate_generator_small_lora_v2_report.md`

Use this manifest only for TypeA LocalDPO-style engineering or smoke tests. Do not scale rollout-based DPO until TypeB candidates are improved.
