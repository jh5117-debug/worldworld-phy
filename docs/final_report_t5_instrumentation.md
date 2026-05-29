# Final Report: T5 Instrumentation

## 1. Current Blocker

The original blocker is still in the LingBot-Fast T5 path, but it is now localized:

- tokenizer succeeds;
- checkpoint stat and read are normal;
- `torch.load` succeeds quickly;
- `load_state_dict` succeeds;
- CPU fp32 model construction and CPU prompt encode are slow;
- GPU bf16 full T5 succeeds.

## 2. Tokenizer

- Tokenizer path: `local_assets/cache/lingbot_fast_cam_runtime/google/umt5-xxl`
- Tokenizer class: `T5TokenizerFast`
- Offline load: success
- Load time: about `3.6-3.8s`

## 3. Checkpoint

- Runtime checkpoint path: `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`
- Realpath: `local_assets/weights/lingbot_base/models_t5_umt5-xxl-enc-bf16.pth`
- Size: `10.582 GiB`
- Stat: normal, symlink to Base checkpoint

## 4. Read Benchmark

- Full read: `25.793s`
- Throughput: `420.094 MiB/s`

## 5. torch.load

- Standard CPU load: `21.895s`
- `weights_only=True`: `21.808s`
- `mmap=True`: `0.111s`
- State dict: `dict`
- Top-level keys: `242`
- Tensor count: `242`
- Dtype: all `torch.bfloat16`
- Largest tensor: `token_embedding.weight`, shape `[256384, 4096]`

`torch.load` is not the blocker.

## 6. T5EncoderModel Init Markers

Standalone staged markers show:

- `model_construct_start` to `model_construct_done`: `263-264s`
- `torch_load_start` to `torch_load_done`: `22.430s`
- `load_state_dict_start` to `load_state_dict_done`: `15.036s`
- CPU `prompt_encode_start` to `prompt_encode_done`: `109.034s`

The slowest init stage is model architecture construction/random initialization before checkpoint load.

## 7. load_state_dict

- Success: yes
- Result: `<All keys matched successfully>`

## 8. dtype / Device Transfer

Standalone probe did not separately time `model.to(dtype/device)` inside `_t5`; it is included in the `model_construct` stage. The generated third-party patch would split these markers if applied.

## 9. Text Embedding

CPU full T5:

- Success: yes
- Shape: `[[6, 4096]]`
- Total elapsed to probe done: about `431s`

GPU bf16 full T5:

- Success: yes
- Shape: `[[6, 4096]]`
- T5 model load: `41.785s`
- Prompt encode: `1.424s`
- Total elapsed to probe done: about `59s`

## 10. Third-Party Instrumentation Patch

- Patch path: `patches/lingbot_t5_instrumentation.patch`
- Intended target: `local_assets/third_party/lingbot_world/wan/modules/t5.py`
- Backup created during one remote attempt: `t5.py.bak_20260529_134344`
- Corrected patch generated and committed.
- Applying the corrected patch on H20 was blocked by intermittent SSH reset/timeouts, so no successful third-party code modification is claimed.

The standalone probe provided equivalent phase timing without modifying third-party logic.

## 11. Gate Decisions

- Official Fast demo: allowed next, because GPU bf16 full T5 now succeeds.
- `cam_physgeo` actual inference: allowed next, with GPU 6/7 and timeout at least `600s`.
- Fast rollout: not allowed yet.
- Reward-on-rollout: not allowed yet.
- VideoGPA encode: not allowed yet.
- DPO: not allowed.

## 12. Next Minimal Action

Run exactly one minimal Fast actual inference with:

- `CUDA_VISIBLE_DEVICES=6,7`
- GPU bf16 T5 path
- timeout `600s` or `900s`
- unbuffered logs
- no training, no rollout batch, no DPO

If that fails, the next blocker is after T5: likely VAE/Fast DiT/pipeline generation rather than T5 checkpoint loading.
