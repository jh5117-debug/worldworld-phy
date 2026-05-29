# T5 Checkpoint Load Probe Report

## Checkpoint Stat

- Path: `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`
- Realpath: `local_assets/weights/lingbot_base/models_t5_umt5-xxl-enc-bf16.pth`
- Size: `11361920418` bytes, `10.582 GiB`
- Symlink: yes

## Read Benchmark

- Bytes read: `11361920418`
- Elapsed: `25.793s`
- Throughput: `420.094 MiB/s` (`0.410 GiB/s`)

Conclusion: storage read bandwidth is not the primary blocker.

## torch.load Only

CPU `torch.load(map_location="cpu")`:

- Elapsed: `21.895s`
- Peak RSS: `11366.87 MiB`
- Object: `dict`
- Top-level keys: `242`
- Tensor count: `242`
- Dtype distribution: all `torch.bfloat16`
- Largest tensor: `token_embedding.weight`, shape `[256384, 4096]`, numel `1050148864`
- First keys include `token_embedding.weight`, `blocks.0.norm1.weight`, `blocks.0.attn.q.weight`, `blocks.0.attn.k.weight`, `blocks.0.attn.v.weight`.

CPU `torch.load(weights_only=True)`:

- Elapsed: `21.808s`
- Peak RSS: `11367.22 MiB`
- Same key/tensor structure.

CPU `torch.load(mmap=True)`:

- Elapsed: `0.111s`
- Peak RSS: `530.98 MiB`
- Same lazy key/tensor structure.

Conclusion: `torch.load` is not the 120s blocker. `mmap=True` is useful for reducing initial RSS and load latency, but model construction remains the main cost.

## Model Construction

`umt5_xxl(encoder_only=True, return_tokenizer=False, dtype=fp32, device=cpu).eval().requires_grad_(False)`:

- Elapsed: `264.233s`
- Peak RSS: `22420.05 MiB`
- Class: `T5Encoder`

Conclusion: the first major blocker is architecture construction/random initialization and dtype/device setup before checkpoint load.

## load_state_dict

Combined CPU staged run:

- Model construction: `263.277s`
- `torch.load`: `22.430s`
- `load_state_dict`: `15.036s`
- Result: `<All keys matched successfully>`
- Peak RSS: `33261.46 MiB`

Conclusion: `load_state_dict` is not the main blocker.

## Full CPU T5

- Tokenizer load: `3.679s`
- T5 model load: `302.903s`
- Prompt encode: `109.034s`
- Embedding shape: `[[6, 4096]]`
- Peak RSS: `33364.98 MiB`

Conclusion: full CPU T5 works with a longer timeout, but it is too slow for a 120s smoke.
