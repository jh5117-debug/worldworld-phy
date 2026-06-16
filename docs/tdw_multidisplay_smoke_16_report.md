# TDW Multidisplay Smoke 16 Report

Status: not run.

Reason: the 8-display precondition is not satisfied. `:9` to `:13` currently report Mesa llvmpipe and `:14/:15` fail. Running TDW smoke under those displays would be misleading and may fall back to CPU/software OpenGL or fail.

Required before smoke:

1. Configure NVIDIA Xorg displays `:9` through `:15`.
2. Confirm `glxinfo -B` reports NVIDIA renderer on every display.
3. Run 16-sample smoke: 8 displays x 2 samples.

Pass criteria remain: at least 15/16 HDF5, each display produces at least one sample, no Xorg crash, no port conflict, validation OK.
