# Pair Energy Audit Summary

- real_backend_available: True
- real_energy_sampled_count: 5
- proxy_energy_count: 61
- full_energy_audit_status: PARTIAL_REAL_SAMPLE_PLUS_PROXY_TRIAGE

The real LingBot-Fast energy backend is available and was already exercised in the tiny DPO probe. For protocol v1, this file records sampled real energies where previous logs match the pair IDs, and reward-proxy triage for the rest. Full all-pair real energy should be run immediately before DPO training, but was not launched here because this task explicitly avoids training and the observed cost is about 192 seconds per DPO step.
