# TDW v2 Warmup Visible-Motion 10-Sample Actual Report

Date: 2026-06-05

## Status

Not run.

## Reason

Actual TDW / Unity generation requires a display. The only verified TDW Xorg display is:

```text
DISPLAY=:8
```

It is bound to GPU0 via:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

This turn explicitly forbids GPU0-5 and requires GPU6/7 only. No GPU6/7 TDW display was found.

The 1-sample visible-motion actual smoke was also not run, so the 10-sample gate remains blocked by dependency.

## Generated Count

- generated HDF5: 0
- accepted samples: 0
- rejected samples: 0
- converted LingBot samples: 0

## Safety

- no GPU0 generation was run;
- no 10-sample visible-motion actual generation was run;
- no 50/200/1k generation was run;
- no training or DPO work was run.
