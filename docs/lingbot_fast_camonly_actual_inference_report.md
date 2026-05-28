# LingBot-Fast Cam-Only Actual Inference Report

## Dry-Run

Dry-run passed the non-GPU checks:

- LingBot-Fast found at `local_assets/weights/lingbot_fast`.
- Fast shards recognized: 16 safetensors plus config.
- Runtime bundle created at `local_assets/cache/lingbot_fast_cam_runtime`.
- Bundle links Base `Wan2.1_VAE.pth`, Base T5, Base tokenizer, and Fast shards under `lingbot_world_fast/`.
- Input sample: `physion_movingcam_07abddf5748b`.
- Prompt: structured Physion P1 prompt.
- Camera motion: `offscreen_z_reobserve`.
- `poses.npy` shape: 81 x 4 x 4.
- `intrinsics.npy` shape: 81 x 4 x 4.
- `metadata.json` has `use_action=false`.
- Dummy `action.npy` exists only for legacy compatibility.

The legacy LingBot code import fails in the default Python because of a `transformers` / `huggingface-hub` version mismatch. Actual smoke uses `LINGBOT_ENV` from config: `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2`.

## Actual Smoke

Command used GPU 6/7 via `CUDA_VISIBLE_DEVICES=6,7`:

```bash
python -m cam_physgeo.eval.run_inference \
  --config configs/cam_physgeo/eval.yaml \
  --model_type fast \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/outputs/smoke/lingbot_fast_inference \
  --smoke-run \
  --limit 1 \
  --num_frames 8 \
  --num_steps 1 \
  --resolution 480x832 \
  --save_contact_sheet \
  --timeout_sec 180
```

Result: failed by timeout.

- Requested frames: 8.
- Normalized Wan frame count: 9, because Wan I2V expects `4n+1` frames.
- Timesteps: `[0]`.
- Elapsed: about 180 seconds.
- Return code: `-9` after timeout kill.
- Output video: not created.
- Contact sheet: not created.
- Log path: `local_assets/outputs/smoke/lingbot_fast_inference/physion_movingcam_07abddf5748b/inference_log.txt`.
- Log content: timeout only, no model stdout before kill.

## Diagnosis

The adapter now reaches the real LingBot-Fast runtime command and passes image, prompt, poses, and intrinsics. It does not use action as a core condition; the sample directory is passed as `action_path` only because `WanI2VFast.generate` expects to find `poses.npy` and `intrinsics.npy` under that argument name. In camera mode it ignores `action.npy`.

The remaining blocker is runtime initialization or first forward taking longer than the allowed short-smoke budget without streaming progress. Next file to improve: `cam_physgeo/eval/run_inference.py`, plus possibly LingBot's `wan/image2video_fast.py` logging/profiling path. Do not generate Fast rollouts until this 1-sample actual inference completes reliably.

