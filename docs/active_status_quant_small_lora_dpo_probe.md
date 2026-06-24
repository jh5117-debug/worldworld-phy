# Active Status: Quant Benchmark + Small-LoRA + DPO Probe Route

Updated: 2026-06-24 16:45 CST

## Current Branch

`research/quant-small-lora-dpo-probe-20260624`

Latest pushed commit at this checkpoint:

`4c42458 Add reward calibration v2 smoke harness`

## Why This Week Looked Worse Than Last Week

The main issue was trainable scope, not prompt quality. Last week's camera-only tiny LoRA changed about 40,960 parameters and mostly stayed inside camera conditioning. This week's broad-LoRA changed about 102.9M parameters across camera conditioning, self-attention, cross-attention, and FFN. That was enough to reduce fixed-val loss while damaging LingBot-Fast's foreground/object/physics prior.

Detailed diagnosis:

`docs/broad_lora_vs_camera_only_diagnosis.md`

## Running Training

Four small-LoRA sweep jobs are running in tmux:

- A: camera-only rank 4 on GPU0,1
- B: camera-only rank 8 on GPU2,3
- C: camera + limited self-attention rank 4 on GPU4,5
- D: camera + limited cross-attention rank 4 on GPU6,7

All four use:

- LingBot-World-Fast
- high-noise-only
- 81 frames
- BF16 mixed-safe
- no StageB
- no DPO training
- no reward pair mining during training

## Step-50 Checkpoints

C checkpoint exists:

`local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_C_camera_self_r4_train200_20260624_141215/checkpoints/small_lora_C_camera_self_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter/adapter_state.pt`

- fixed-val loss: 0.125559
- gate: PASS

D checkpoint exists:

`local_assets/experiments/small_lora_scope_sweep_20260624/train/small_lora_D_camera_cross_r4_train200_20260624_141215/checkpoints/small_lora_D_camera_cross_r4_train200_20260624_141215/high_only_phase/branches/step_000050/fast_stageA_high_noise_adapter/adapter_state.pt`

- fixed-val loss: 0.125559
- gate: PASS

A/B have not reached step50 yet and are slower because they match many more camera-conditioning linears.

## Why Rollout Has Not Started Yet

All GPUs 0-7 are currently occupied by the four sweep trainings. Fast inference/rollout is expected to need substantial GPU memory, so running it concurrently would likely OOM or destabilize the sweep. The correct next action is to wait until at least one 2-GPU group completes or is explicitly stopped by user instruction.

## Implemented This Round

- Quantitative Benchmark v1 manifests and evaluator.
- Structured video audit/contact-sheet tooling.
- Quality-bounded anchored DPO pair builder.
- Reward Calibration v2 smoke harness.
- Fast inference wrapper now supports explicit `--allow_gpu0` after user approval.
- PRDs updated for benchmark, small-LoRA sweep, reward calibration, and DPO probe.

## DPO Data Strategy

Winner can be clean GT.

Loser must not be a collapsed video. Use quality-bounded hard negatives only:

- clean GT vs controlled corrupted GT
- clean GT vs quality-qualified bad rollout
- high-quality rollout winner vs worse rollout only if winner absolute quality passes

Broad-LoRA outputs are only valid as losers if they pass the same quality floor.

## Next Action When GPU Frees

1. Generate probe rollouts for Original Fast, last-week camera-only tiny LoRA, C step50, and D step50.
2. Run `cam_physgeo.eval.video_audit` on every generated video.
3. Run `cam_physgeo.eval.quant_benchmark_v1` on the probe set.
4. Build quality-bounded pairs with `cam_physgeo.dpo.quality_bounded_pairs` only after quality floor passes.
5. Run DPO BF16 preflight before any DPO probe.

## Not Done Yet

- No rollout from C/D step50 yet.
- No full Quant Benchmark model comparison yet.
- No full Reward Calibration v2 yet.
- No DPO BF16 preflight yet.
- No DPO probe yet.
- No StageB.
- No large full-data StageA.
