# GPU Usage Approval Request: TDW Generation v2 Actual Smoke

## Task

TDW / Physion-style moving-camera v2 actual generation smoke for `warmup_mild`.

## Why Approval Is Needed

The current task permits small smoke jobs only on GPU 6/7. The H20 process audit showed the TDW/Unity Xorg display process:

`/usr/lib/xorg/Xorg :8 -config /etc/X11/tdw-xorg-gpu0.conf ...`

This indicates that the configured TDW display `:8` is likely bound to GPU0, not GPU6/7. Starting TDW/Unity actual generation on that display may therefore violate the current GPU rule.

## Expected GPU Use

- Task: 1-sample TDW generation smoke
- Display: `:8`
- Observed display GPU: GPU0
- Allowed GPUs this round: GPU6, GPU7
- Expected memory: unknown until Unity starts
- Expected runtime: short for 1 sample, but graphics context may still use GPU0

## Alternatives

- Configure a TDW/Unity display on GPU6/7.
- Run CPU/headless only if TDW supports it in this environment.
- Keep only plan/validator dry-runs until display routing is fixed.
- Ask user to approve GPU0 specifically for a one-sample TDW smoke.

## Requested Confirmation

Please confirm one of the following before actual TDW generation:

1. Provide/approve a TDW display bound to GPU6/7.
2. Explicitly approve a one-sample smoke on the existing GPU0-bound display.
3. Keep actual generation blocked and only proceed with wrapper/plan/validator work.

