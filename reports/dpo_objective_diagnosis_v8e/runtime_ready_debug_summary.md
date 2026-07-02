# v8e Runtime-Ready Debug Summary

Current Status:
BLOCKED

Updated: 2026-07-02 17:47 CST

## What Ran

- H20 GPU7 was used via `CUDA_VISIBLE_DEVICES=7`.
- Command: `python3 -m cam_physgeo.dpo.winner_anchor_runtime_ready_debug`.
- Input pair: first reviewed GT>C pair from `manifests/dpo_smoke_v7_gt_c_10.jsonl`.
- No DPO, SDPO, Linear-DPO, Safe-linear, StageB, GRPO, full-data StageA, broad-LoRA, cache training, or pair factory rollout was run.

## Environment Fixes Applied

The system Python was missing runtime packages. User-level pip installs were applied on H20-2:

- `opencv-python-headless==4.10.0.84`
- `decord==0.6.0`
- `easydict==1.13`
- `diffusers==0.32.2`
- `peft==0.14.0`
- `timm==1.0.12`
- `mpmath==1.3.0`
- `ftfy==6.3.1`
- `scipy==1.15.3`

## Stage Results

- `0_initial`: PASS
- `1_parse_manifest`: PASS
- `2_select_pair`: PASS
- `3_resolve_paths`: PASS
- `4_decode_winner_video_cpu`: PASS, about 29-32 seconds
- `5_select_window_indices`: PASS
- `6_load_policy_runtime`: TIMEOUT_RUNNING

`stage 6_load_policy_runtime` produced heartbeats through about 266 seconds but did not complete and did not allocate GPU memory on GPU7. The process was stopped after timeout to avoid an unbounded run.

## Decision

`RUNTIME_READY_BLOCKED_6_LOAD_POLICY_RUNTIME_TIMEOUT`

The current blocker is not GPU availability, sigma mapping, or video decode. It is policy runtime initialization before GPU allocation. Next work should split `load_policy_runtime` into smaller sub-stages: import Wan/LingBot modules, resolve checkpoint/config, instantiate text/DiT/VAE components, load adapter, move model to GPU, and report each step separately.
