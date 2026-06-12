# GPU Usage Approval Request: TDW v5 1k Generation

Date: 2026-06-11

## Request

Approve a separate TDW v5 aggressive visible-motion 1k generation run.

## Current Blocker

The only confirmed TDW display is GPU0-bound:

- `DISPLAY=:8`
- `/etc/X11/tdw-xorg-gpu0.conf`

No GPU4-7 TDW display is currently configured.

## Options

Option A: approve GPU0 / `DISPLAY=:8` for TDW v5 1k generation.

Option B: configure a GPU4-7 TDW Xorg display and then run generation there.

## Safety

- This request is for TDW generation only.
- It does not approve DPO.
- It does not approve VideoGPA 03_train.
- It does not approve Stage1.
- It does not approve full model finetune.

## Proposed Next Command After Approval

Generate a v5 1k plan, validate it, run TDW generation on the approved display, convert accepted samples to LingBot cam-only format, and update the dataset registry.
