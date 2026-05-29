# T5 GPU Probe Report

## Preconditions

GPU probe was only run after CPU staged probes succeeded.

Before launch, GPUs 6 and 7 showed:

- GPU 6: `1 MiB`, `0%`
- GPU 7: `1 MiB`, `0%`

Command used `CUDA_VISIBLE_DEVICES=6,7`.

## Result

Stage: `full_t5`

- Device: `cuda`
- Dtype: `bf16`
- Tokenizer load: `3.808s`
- T5 model load: `41.785s`
- Prompt encode: `1.424s`
- Embedding shape: `[[6, 4096]]`
- Probe result: success

## Memory

During the first poll, GPU 6 showed about `24058 MiB`; GPU 7 showed `4 MiB`.

After the probe ended, `pgrep` did not show the probe process. A later `nvidia-smi` check showed GPU 6/7 memory in use by other activity, but no cleanup or kill was performed because the user prohibited process management outside this debug task.

## Interpretation

GPU bf16 T5 is viable and much faster than CPU fp32:

- CPU full T5: about `431s`
- GPU bf16 full T5: about `59s`

The original 120s CPU timeout is too short; the Fast runtime should prefer GPU bf16 T5 for inference smoke.
