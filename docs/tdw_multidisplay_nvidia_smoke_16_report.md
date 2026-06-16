# TDW Multidisplay NVIDIA Smoke 16 Report

Status: not run.

Reason: insufficient NVIDIA displays.

- Required: at least two NVIDIA displays, ideally `:8,:20,:21,:22,:23,:24,:25,:26`.
- Available now: only `:8` is NVIDIA.
- `:9` to `:13` are llvmpipe and are explicitly rejected.
- `:20` to `:26` do not exist yet.

No TDW samples were generated in this phase.

Next step: configure NVIDIA Xorg displays as root, verify renderer, then run 16-sample smoke.
