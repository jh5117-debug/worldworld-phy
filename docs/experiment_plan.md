# Experiment Plan

Stage 0: reward calibration and camera audit, no training.

Stage 1: light support warm-up with LoRA/adapters only, low LR, short schedule, replay, TRD auxiliary, and reward early stopping.

Stage 2: anchored DPO as the main method. Pair types: clean GT over corrupted GT, clean GT over bad Fast rollout, teacher over Fast, and a small amount of filtered self-rollout.

Stage 3: self-rollout DPO only after pass@K, quality, background/camera, and margin gates pass.

Stage 4: optional online GeoFlow-style RL/GRPO only after the reward is calibrated and the base rollout quality is adequate.
