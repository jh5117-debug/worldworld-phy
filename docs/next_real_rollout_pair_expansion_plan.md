Current Status: READY_PLAN_ONLY

# Next Real Rollout Pair Expansion Plan

This is a plan only. No rollout or training was run in v10b.

## Current State

- Real rollout-derived trainable pairs: 15
- Controlled synthetic / TypeA_plus pairs: 66
- Current real rollout expansion blocker: WanI2VFast initialization / policy runtime loading stalls before reliable large-scale rollout.

## Goal

Recover a real rollout-derived pair factory with at least 50 reviewed GT>C or B>C medium-hard pairs.

## Plan

1. Reuse the safe Wan loader diagnosis path from v8f/v8g.
2. Patch the V2V-5 / WanI2VFast inference runner to avoid black-box `from_pretrained` stalls.
3. Run a 1-condition smoke with M0, B camera-r8, and C camera+self-temporal-r4.
4. If smoke passes, run 16 conditions, then 32 conditions.
5. For every candidate loser, generate contact sheets and require Codex visual audit.
6. Reject blurry, collapsed, black-screen, too-similar, or unexplained failures.
7. Build GT>C first; build B>C only when B winner quality passes.
8. Target at least 50 real rollout-derived DPO-ready pairs.

## Non-Goals

- Do not mix synthetic controlled pair counts into real rollout pair counts.
- Do not run DPO until pair data and winner-side objective gates pass.
- Do not push MP4/JPG/PNG/local_assets/checkpoints.
