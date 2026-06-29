# Candidate Generator Small-LoRA v2 Report

Current Status: BLOCKED_WAITING_FOR_GPU_CAPACITY
Updated: 2026-06-29 15:39:49

## Trigger

Protocol v2 rejected all Type B rollout losers: 16 / 16 failed the sharpness-ratio gate and 10 / 16 failed the per-condition R_quality p40 gate. This means rollout-based medium-hard losers are not usable yet.

## Current Round Result

Candidate-generator v2 was not launched because all physical GPUs 0-7 were occupied by an unrelated LIBERO evaluation, with roughly 25-50 GB already used per GPU. Previous DPO/LingBot energy and generation paths reserve high memory, so launching would risk OOM and interfere with another workload.

## Planned Models Once GPU Capacity Is Available

- G0: Original Fast baseline, no train.
- G1: old camera-only tiny LoRA, no new train.
- G2: camera-only rank8, 100 steps.
- G3: camera + limited temporal/self-attn rank4, max 4 blocks, 100 steps.
- G4: optional mixed high/mid/low-noise detail refinement.

## Decision

Do not use current Type B rollout losers. Protocol v3 remains TypeA-only until candidate generator v2 can be run and produces sharp, quality-qualified medium-hard rollout losers.
