Current Status:
PRD_PREPARED_NOT_EXECUTED

# DPO Objective Diagnosis v8c Status

Updated: 2026-07-02 06:20 CST

## Readback

- v7 tiny SDPO-anchor DPO smoke was engineering-stable but objective-signal failed: final winner improvement was negative, loser degradation was positive, and final winner contribution ratio was 0.0.
- v8 full real-energy sigma check on 10 reviewed GT>C pairs timed out before objective training.
- v8b bounded diagnosis proved sigma/timestep mapping is separated:
  - sampler-only low/mid/high means: 0.125125 / 0.399900 / 0.824925.
  - real-energy one-pair low/mid/high actual sigmas: 0.1243339181 / 0.3495545387 / 0.8247423172.
- v8b winner-anchor-only requested 1 pair for 5 steps but completed only 1 step, with nonzero grad, objective loss 0.1511940509, winner improvement 0.0, then CUDA OOM.

## Connectivity Correction

The previous v8c attempt did not execute any experiment because Codex was running on `hal-9000`, where the target repo was not mounted and SSH alias resolution failed. This status file is written after reconnecting directly to H20-2 via `ssh -i ~/.ssh/codex_h20_2 ubuntu@27.190.15.128` and confirming the target repo.

## Current Blocker

Sigma/timestep mapping is not the current blocker. The active blocker is that the true winner-anchor-only training graph is not memory-safe for even 1 pair / 5 steps.

## v8c Goal

Run a memory-safe winner-anchor-only diagnosis that removes loser and reference work from the training graph, caches winner latents, and recomputes policy winner energy after each optimizer update.

## Explicit Non-Runs

This round does not run standard DPO, strict SDPO, Linear-DPO, safe-linear DPO, large-scale DPO, StageB, GRPO, full-data StageA, broad-LoRA, pair factory rollout, or checkpoint/video generation.
