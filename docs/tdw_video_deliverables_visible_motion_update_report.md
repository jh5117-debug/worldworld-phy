# TDW Video Deliverables: Visible-Motion Update Report

Date: 2026-06-05

## Status

No new visible-motion videos were added.

## Reason

Actual `warmup_visible_motion` generation was blocked by the missing GPU6/7 TDW display.

The GPU6/7 setup audit found:

- GPU6 and GPU7 are idle;
- only `DISPLAY=:8` is verified;
- `DISPLAY=:8` is bound to GPU0;
- passwordless sudo is unavailable, so Codex could not create or start a GPU6/7 Xorg display.

The existing 50-sample videos remain indexed, but they are now marked in project documentation as pipeline validation samples with camera motion too weak for final warmup main data.

Next update should add a new category after generation succeeds:

`TDW v2 warmup_visible_motion 10-sample smoke`
