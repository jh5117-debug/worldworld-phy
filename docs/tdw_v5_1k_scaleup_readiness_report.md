# TDW v5 1k Scale-Up Readiness Report

Date: 2026-06-11

## Decision

TDW v5 1k generation was not started in this run.

## Reason

The current confirmed TDW / Unity display is:

- `DISPLAY=:8`
- Xorg config: `/etc/X11/tdw-xorg-gpu0.conf`
- Bound GPU: GPU0

No `/etc/X11/*gpu4*`, `/etc/X11/*gpu5*`, `/etc/X11/*gpu6*`, or `/etc/X11/*gpu7*` TDW display config was found.

The current run allows GPU4-7 for LingBot warmup / rollout / reward. It does not explicitly approve GPU0 / `DISPLAY=:8` for TDW 1k generation. Therefore 1k TDW generation is blocked pending either:

1. explicit GPU0 / `DISPLAY=:8` approval for TDW v5 1k generation, or
2. admin setup of a GPU4-7 TDW Xorg display.

## Current Dataset Sufficiency

The existing TDW v5 200 human-approved dataset is sufficient to continue the warmup pipeline:

- 200/200 LingBot converted.
- train/val/test split exists.
- Dataloader and true forward-loss gate passed.
- 60-step balanced Stage A smoke passed.

## Recommendation

Continue the warmup / rollout / reward-pair pipeline on v5 200 first. Request TDW 1k generation separately.
