# Final Report: LingBot-Fast T5 Debug

## 1. Current Blocker

The highest-priority blocker is still LingBot-Fast T5/text encoder initialization.

Known from the previous successful probes:

- `torch` import succeeds.
- CUDA is visible in the LingBot env.
- `wan` import succeeds.
- `WanI2VFast.__init__` times out.
- A narrower T5-only probe reaches `T5EncoderModel(...)` and times out.

This points to Base T5/tokenizer/checkpoint initialization, not to Physion camera paths, dummy `action.npy`, or VideoGPA.

## 2. Tokenizer Probe

Added `cam_physgeo/eval/probe_lingbot_t5.py`.

The new probe can load tokenizer and T5 separately from `WanI2VFast`, prints flushed JSON markers, supports offline/local-only mode, and records embedding shape if prompt encoding succeeds.

The new probe could not be completed on H20 in this pass because SSH repeatedly reset or timed out during command execution. No tokenizer success is claimed.

## 3. T5 Model Probe

The code path is ready:

```bash
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cpu \
  --dtype fp32 \
  --local-files-only \
  --timeout 120
```

For H20, use `python3` or `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python` because `python` was not found in one shell attempt.

No new embedding shape is available yet.

## 4. Official LingBot-Fast Demo

Candidate official scripts were identified under `local_assets/third_party/lingbot_world`:

- `generate_fast.py`
- `run_fast.sh`
- `wan/image2video_fast.py`

The official minimal inference was not run because SSH became unstable before script inspection and command construction completed. No official output video exists from this pass.

## 5. Cam-PhysGeo Dry-Run

`cam_physgeo/eval/run_inference.py` now supports:

- direct `LINGBOT_ENV/bin/python -u` instead of buffered `conda run`;
- `--timeout`;
- `--local-files-only`;
- `--probe-only`;
- explicit `--text-embedding-cache` and `--skip-t5-if-cached` flags;
- flushed runtime markers around import, image load, pipeline init, generate, and save.

The H20 dry-run v2 did not complete because SSH reset before the command returned. The patch itself compiled and passed local tests.

## 6. Actual Short Inference

Not run in this pass. No video was generated.

Reason: this pass only added the T5 probe/logging path and could not complete H20 commands due SSH resets. The prior actual short inference still stands: it timed out before producing video.

## 7. Failure Classification

Current likely failure class:

- T5/tokenizer/checkpoint initialization latency or hang.

Not currently supported by evidence:

- Missing Physion `poses.npy` / `intrinsics.npy`.
- `action.npy` being used as a core model condition.
- VideoGPA involvement.
- DPO/training issue.

Still to confirm:

- exact `transformers` version in the LingBot env;
- whether tokenizer alone loads successfully offline;
- whether the T5 checkpoint load is CPU-bound, disk-bound, version-bound, or waiting on HuggingFace;
- whether official `generate_fast.py` fails in the same place.

## 8. Cached Text Embedding

`probe_lingbot_t5.py` supports `--save_embedding`, but cached embedding bypass is not wired into `WanI2VFast`.

`run_inference.py` now accepts `--text-embedding-cache` and `--skip-t5-if-cached`, but refuses to fake success because `WanI2VFast` currently constructs T5 in `__init__`.

## 9. Gate Status

- Fast actual inference: not passed.
- Fast rollout: not allowed.
- Reward-on-rollout: not allowed.
- VideoGPA encode: not the current priority.
- DPO: not allowed.

Only after actual Fast inference generates a video should the next round move to Fast rollout and reward-on-rollout.

## 10. Next Minimal Action

When SSH is stable, run:

```bash
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work
git checkout physion-lingbotfast-t5-debug

PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 $PY -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cpu \
  --dtype fp32 \
  --local-files-only \
  --timeout 120 \
  --out local_assets/reports/smoke/lingbot_t5_probe_cpu.json
```

If tokenizer succeeds and T5 stalls again, inspect `local_assets/third_party/lingbot_world/wan/modules/t5.py` around checkpoint loading and tokenizer construction.
