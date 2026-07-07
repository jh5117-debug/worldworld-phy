# v14 Real-Energy CUDA Runtime Pass Summary

Generated: `2026-07-08T04:39:56`

Decision: `REAL_ENERGY_ONEPAIR_CUDA_RUNTIME_PASS`

## What Changed

The previous one-pair real-energy stage debug with `runtime_device=cpu` timed out at `7_encode_winner_probe`. The same asset-complete pair was rerun with `runtime_device=cuda` on physical GPU4.

## Result

- Pair: `v11_SYN_0017_02215_collision_strafe_left_180_seed41215_background_drift_visible`
- Status: `ok`
- Energy seconds: `212.44250082969666`
- Policy winner energy: `0.13607239723205566`
- Policy loser energy: `0.15526923537254333`
- Ref winner energy: `0.13607239723205566`
- Ref loser energy: `0.15526923537254333`
- Sigma: `0.9540635943412781`
- Timestep index: `325`
- CUDA peak memory GB: `50.43468189239502`

## Interpretation

The VAE/energy timeout blocker is specifically the CPU runtime path. Keeping VAE/runtime on CUDA allows one asset-complete pair to finish and write a real energy row. This is a calibration-path repair, not a DPO recipe.

## Remaining DPO Decision

`DPO_RECIPE_NOT_FOUND_V14` remains unchanged because E09/E10 still fail the true V2V-5 visual gate. No S16/S32/train400 scale is allowed from this result alone.

## Safe Next Step

Use `runtime_device=cuda` for bounded real-energy calibration on S_pass/stratified small subsets, with strict GPU4/5 scheduling and memory caps, before any renewed objective search.
