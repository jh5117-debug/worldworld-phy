# LingBot T5 Probe Report

## Added Probe

New entry point:

```bash
python -m cam_physgeo.eval.probe_lingbot_t5
```

Capabilities:

- loads tokenizer separately from `WanI2VFast`;
- loads LingBot/Wan `T5EncoderModel` separately;
- optionally encodes one prompt and reports embedding shape;
- prints JSON markers with `flush=True` before each step;
- supports `--local-files-only`, `--offline`, `--device cpu|cuda`, `--dtype fp32|fp16|bf16`, `--path`, `--prompt`, `--timeout`, and `--save_embedding`;
- sets offline HuggingFace env vars when requested;
- does not initialize `WanI2VFast`;
- does not train or run video generation.

## Intended Commands

CPU:

```bash
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cpu \
  --dtype fp32 \
  --local-files-only \
  --timeout 120
```

GPU 6/7:

```bash
CUDA_VISIBLE_DEVICES=6,7 TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cuda \
  --dtype bf16 \
  --local-files-only \
  --timeout 120
```

On H20, the default `python` command was not found during one SSH attempt; use `python3` for the project dry-run or the LingBot env Python at `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python` for the real T5 probe.

## Current Run Status

The code was pushed and pulled into the H20 auxiliary worktree, but the live H20 SSH connection repeatedly reset or timed out before the new CPU/GPU probe commands completed. Therefore this report does not claim tokenizer or T5 success.

Known from previous probes:

- `torch` import succeeded in the LingBot env.
- CUDA was visible.
- `wan` import succeeded.
- `WanI2VFast.__init__` timed out.
- A T5-only constructor probe reached `T5EncoderModel(...)` and timed out.

## Current Answers

- Tokenizer success: not yet re-tested with the new probe.
- T5 config success: not yet re-tested with the new probe.
- T5 weights success: not yet re-tested with the new probe.
- Embedding shape: not available.
- Failure class from previous probe: likely T5/tokenizer/checkpoint initialization latency or hang, not camera-condition adapter logic.
- Download issue: active offline flags are now available; next probe should confirm whether any code tries to access HuggingFace.
- Version issue: `probe_lingbot_t5.py` records `transformers.__version__` when it runs.
