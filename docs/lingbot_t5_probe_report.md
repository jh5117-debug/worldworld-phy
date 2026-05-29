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

The CPU probe ran in the H20 auxiliary worktree with the LingBot official environment:

```bash
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 timeout 240s $PY -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --device cpu \
  --dtype fp32 \
  --local-files-only \
  --timeout 120 \
  --out local_assets/reports/smoke/lingbot_t5_probe_cpu.json
```

Result: failed at T5 model load timeout.

Observed markers:

- `import_transformers_done`: version `4.51.3`.
- `tokenizer_load_done`: class `T5TokenizerFast`, elapsed `3.583s`.
- `import_torch_done`: version `2.11.0+cu128`, CUDA available.
- `t5_model_load_start`: checkpoint `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`, size `10.582GB`.
- `probe_failed`: `StepTimeout('t5_model_load exceeded 120s')`, elapsed `134.493s`.

The GPU T5 probe was not run because the requested sequence was "if CPU succeeds, then GPU"; CPU did not succeed.

Known from previous probes:

- `torch` import succeeded in the LingBot env.
- CUDA was visible.
- `wan` import succeeded.
- `WanI2VFast.__init__` timed out.
- A T5-only constructor probe reached `T5EncoderModel(...)` and timed out.

## Current Answers

- Tokenizer success: yes.
- T5 config success: not separated from `T5EncoderModel` construction by the current probe; the failure occurs in the combined `load_wan_t5(...)` call after `t5_model_load_start`.
- T5 weights success: no; timeout while loading/constructing T5 from the 10.582GB checkpoint.
- Embedding shape: not available.
- Failure class: T5 checkpoint/model initialization latency or hang, not tokenizer and not camera-condition adapter logic.
- Download issue: unlikely for tokenizer because it loaded offline from local files; still possible inside custom Wan T5 construction only if that code bypasses offline controls.
- Version: `transformers==4.51.3`, `torch==2.11.0+cu128`.
