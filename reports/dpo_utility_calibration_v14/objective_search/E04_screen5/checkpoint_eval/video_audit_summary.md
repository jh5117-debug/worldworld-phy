# E04_screen5 Codex Video Audit

- Reviewed contact sheets: `8/8`
- Checkpoints: `step000`, `step005`
- Training signal: `TRAINING_SIGNAL_PASS`
- Visual gate: `FAIL`
- Step005 worse count: `3/4`
- Decision: `WINNER_BACKBONE_SIGNAL_ONLY_VIDEO_FAIL_V14`

Findings:
- E04 deletes lose-gap and gives a cleaner winner-energy signal, but video quality still degrades.
- Step005 introduces duplicate foreground objects, text-like wall artifacts, and object-count drift in multiple validation samples.
- E04 is useful as a diagnostic winner-preserving backbone, not as a full DPO recipe.

Scale decision: `NO_SCALE`.
