# EXP V2V-5 Rollout Scoring

Status: prepared

Goal: score V2V-5 candidate rollouts with a quality floor before building anchored DPO pairs.

Inputs: prefix frames 0-4, prompt, poses, intrinsics; generated/evaluated target is future frames 5-80.

Gate: reject black/collapsed/frozen/scene-replaced outputs; losers must be hard negatives, not trivially broken videos.
