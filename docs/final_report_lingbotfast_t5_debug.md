# Final Report: LingBot-Fast T5 Debug

## 1. Current Blocker

The highest-priority blocker is still LingBot-Fast T5/text encoder initialization.

Confirmed by the latest CPU T5 probe:

- `transformers` imports successfully: version `4.51.3`.
- tokenizer loads successfully offline as `T5TokenizerFast` in `3.583s`.
- `torch` imports successfully: version `2.11.0+cu128`.
- CUDA is visible in the LingBot env.
- T5 model construction/checkpoint load starts from `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`.
- The T5 checkpoint is present and about `10.582GB`.
- `t5_model_load` times out after `120s`.

This points to Base T5 checkpoint/model initialization, not tokenizer, Physion camera paths, dummy `action.npy`, or VideoGPA.

## 2. Tokenizer Probe

`cam_physgeo/eval/probe_lingbot_t5.py` ran far enough to prove tokenizer success:

- tokenizer root: `local_assets/cache/lingbot_fast_cam_runtime/google/umt5-xxl`
- files present: `spiece.model`, `tokenizer.json`, `tokenizer_config.json`
- missing in tokenizer root: `config.json`
- result: `T5TokenizerFast` loaded successfully offline

## 3. T5 Model Probe

CPU command used:

```bash
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 $PY -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cpu \
  --dtype fp32 \
  --local-files-only \
  --timeout 120
```

Result:

- T5 config/model construction: did not complete.
- T5 weights: did not complete loading.
- Failure: `StepTimeout('t5_model_load exceeded 120s')`.
- Embedding shape: unavailable because prompt encoding was never reached.

The GPU T5 probe was not run because CPU did not succeed.

## 4. Official LingBot-Fast Demo

Candidate official scripts were identified under `local_assets/third_party/lingbot_world`:

- `generate_fast.py`
- `run_fast.sh`
- `wan/image2video_fast.py`

The official minimal inference was not run after CPU T5 failed. It would hit the same T5 initialization path before generation, and GPU 6 was also partially occupied during the initial check. No official output video exists from this pass.

## 5. Cam-PhysGeo Dry-Run

`cam_physgeo/eval/run_inference.py` now supports:

- direct `LINGBOT_ENV/bin/python -u` instead of buffered `conda run`;
- `--timeout`;
- `--local-files-only`;
- `--probe-only`;
- explicit `--text-embedding-cache` and `--skip-t5-if-cached` flags;
- flushed runtime markers around import, image load, pipeline init, generate, and save.

The cam_physgeo dry-run was not re-run after the T5 failure because it does not initialize T5 and would not resolve the current blocker. The code path remains ready with unbuffered logging and local-only flags.

## 6. Actual Short Inference

Not run in this pass. No video was generated.

Reason: CPU T5 probe failed before model embedding could be produced. The prior actual short inference still stands: it timed out before producing video.

## 7. Failure Classification

Current likely failure class:

- T5 checkpoint/model initialization latency or hang.

Not currently supported by evidence:

- Missing Physion `poses.npy` / `intrinsics.npy`.
- `action.npy` being used as a core model condition.
- VideoGPA involvement.
- DPO/training issue.

Still to confirm:

- whether the T5 checkpoint load is CPU-bound, disk-bound, version-bound, or blocked inside custom Wan model construction;
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

Next run should instrument `local_assets/third_party/lingbot_world/wan/modules/t5.py` inside `T5EncoderModel.__init__` to separate:

- config construction;
- tokenizer reuse;
- checkpoint `torch.load`;
- state dict mapping;
- device transfer;
- dtype conversion.

Minimal rerun:

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

Since tokenizer already succeeded and T5 stalled, inspect `local_assets/third_party/lingbot_world/wan/modules/t5.py` around checkpoint loading and model construction before attempting rollout/reward/VideoGPA/DPO.
