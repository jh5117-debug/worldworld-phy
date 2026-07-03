Current Status: PASS

# DPO Pair Factory v10b Status

Generated: 2026-07-03 22:16:34

- v10 ready pairs audited: 81.
- Strict-ready/trainable: 81.
- Diagnostic-only: 0.
- Rejected: 0.
- Real rollout-derived GT>C: 15.
- Controlled synthetic TypeM-v10: 63.
- TypeA_plus controlled: 3.
- Top50 balanced subset: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`.
- PPT showcase video already exists: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_ready_showcase.mp4`.
- Main caveat: synthetic controlled negatives are not real rollout losers.
- This round only performed audit/freeze/subset/documentation. No training or DPO was run.
