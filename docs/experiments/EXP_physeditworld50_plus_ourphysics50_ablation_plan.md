# EXP PhysEditWorld50 Plus OurPhysics50 Ablation Plan

## Purpose

This is a future ablation plan only. It is not run in the current PhysEditWorld 50h prompt-gravity baseline round.

## Conditions

A. PhysEditWorld 50h only.

B. PhysEditWorld 50h plus our physics 50h.

## Why Not Mix First

PhysEditWorld contains matched replay semantics: action trace, camera trajectory, intrinsics, gravity label, and target future video. Much of our existing physics data is passive camera-conditioned data and may not carry matched action/gravity replay semantics. Mixing too early may confuse action, dummy-action, camera, and gravity tokens.

## Comparison Metrics

- Gravity response.
- Camera/background stability.
- Object physics.
- Reobserve consistency.
- Visual quality.
- Freeze rate.
- Artifact/identity drift.
- Action/dummy-action semantic confusion.

## Gate

Only run this ablation after the PhysEditWorld 50h-only pipeline has:

- valid selected 50h manifest;
- prompt-only conversion smoke;
- baseline rollout;
- rank32 warm-up gates;
- checkpoint video + metrics + Codex visual audit.

No StageB, GRPO, broad-LoRA, or large DPO is part of this ablation plan.
