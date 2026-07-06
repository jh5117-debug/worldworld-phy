# DPO Objective Search v13b Interim Summary

S01 and S02 were run only on physical GPU4/5 and were stopped after the first healthy training-signal window so checkpoint video/metric gates can be evaluated before launching more schemes.

- S01_winner_detached_pref_low: rows=53 last_step=52 mean50_winner_improvement=0.0005808174610137939 latest=0.0014492273330688477 mean50_ratio=0.9542738120644342 decision=TRAINING_SIGNAL_PASS_NEEDS_VIDEO_METRICS
- S02_winner_detached_pref_lower_lr: rows=54 last_step=53 mean50_winner_improvement=0.00019512534141540526 latest=0.00029265880584716797 mean50_ratio=0.8764944013781223 decision=TRAINING_SIGNAL_PASS_NEEDS_VIDEO_METRICS

Current status: training signal only. No DPO recipe is valid until checkpoint videos, metrics, and Codex visual audit pass.
