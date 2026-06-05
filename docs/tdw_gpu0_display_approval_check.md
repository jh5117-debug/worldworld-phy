# TDW GPU0 Display Approval Check

Date: 2026-06-05

## Display

Current TDW display:

```text
DISPLAY=:8
```

The display is available:

```text
display_8_ok
```

It is backed by:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

The Xorg config binds `DISPLAY=:8` to GPU0:

```text
BusID "PCI:82:0:0"
```

## GPU Status Before Smoke

GPU0 was idle enough for the approved smoke:

```text
0, 00000000:52:00.0, 28 MiB, 97871 MiB, 0 %
```

## Approval Scope

The user explicitly approved GPU0 / `DISPLAY=:8` only for:

- one `warmup_visible_motion` actual sample;
- ten `warmup_visible_motion` smoke samples if the one-sample gate passed.

This approval does not cover:

- 50 samples;
- 200 / 1k+ samples;
- training;
- DPO training;
- VideoGPA `03_train`;
- Stage1;
- LingBot rollout;
- reward calibration.
