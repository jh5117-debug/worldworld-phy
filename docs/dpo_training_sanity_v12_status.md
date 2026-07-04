Current Status: DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL

# DPO Training Sanity v12 Status

- Canonical data entry: `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`.
- Repaired splits used: train400 / val50 / test50 / top50.
- S0 scope probe cache: `16/16 PASS`.
- LoRA scope decision: only `L0_camera_r4` passed winner-anchor sanity.
- L1 camera-r8 failed: final winner improvement negative.
- L2 camera+temporal failed: final winner improvement non-positive.
- L3 camera+cross failed: mean/final winner improvement negative.
- S1 tiny DPO cache: `32/32 PASS`.
- S1 guarded SDPO-anchor run: stopped at 11 rows / step10 due winner-worse and no-signal behavior.
- Mean winner_improvement_post: `-7.748603820800781e-07`.
- Final winner_improvement_post: `-0.00018405914306640625`.
- Mean winner_contribution_ratio_post: `0.43831473876668603`.
- Final winner_contribution_ratio_post: `0.0`.
- DPO loss stayed near `0.6931492632085626`.
- Checkpoints saved locally: step0/5/10 only; no videos are pushed.
- Checkpoint video eval was not run because the energy signal already triggered early STOP; no PASS is claimed.

Decision: `DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`.

Safety: no large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, no data/weights/video pushed.
