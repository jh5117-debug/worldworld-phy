# GPU Approval Request: TDW v5 Dataset Scale-Up

Date: 2026-06-10

## Request

Approve a bounded TDW v5 aggressive 2x data scale-up only after choosing the TDW display resource.

## Why Approval Is Needed

TDW/Unity uses Xorg `DISPLAY`. The confirmed usable display in prior audits is GPU0-bound `DISPLAY=:8`; GPU4-7 CUDA availability is not enough for TDW generation.

## Options

Option A: approve GPU0 / `DISPLAY=:8` for bounded TDW generation.

Option B: configure a GPU4-7 TDW Xorg display and then run generation there.

Option C: defer TDW scale-up and continue with the existing v5 200 dataset.

## Safety

No DPO, no VideoGPA `03_train`, no Stage1, no reward calibration, and no full model checkpoint are part of this request.
