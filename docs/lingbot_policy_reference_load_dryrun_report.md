# LingBot Policy / Reference Load Dry-Run Report

## Result

- Status: passed.
- Runtime class: `WanI2VFast`.
- Policy DiT class: `WanModelFast`.
- Runtime checkpoint dir: `local_assets/cache/lingbot_fast_cam_runtime`.
- Device: `cuda:0` under `CUDA_VISIBLE_DEVICES=6,7`.
- Dtype: `bfloat16`.
- Scheduler: `FlowUniPCMultistepScheduler`.
- `num_train_timesteps`: `1000`.
- Model mode: eval.
- Trainable parameters after freeze: `0`.
- Parameter count: `23,788,851,264`.
- Policy load time: about `446-464s`.
- CUDA allocation after load: about `48.19 GB`.

## Reference Status

The reference model is explicit but deferred. It is intended to be a frozen
same-weight LingBot-Fast copy. Loading a second full model would roughly double
memory for this 1-pair no-optimization dry-run, so this round only computed
policy energies.

## Safety

- No backward.
- No optimizer.
- No LoRA save.
- No parameter update.
- Optional physics adapter was forced disabled for the adapter path:
  `physics_adapter_enabled=false`.

The Hugging Face loader still reports missing `physics_*` keys because those
optional modules exist in the model class/config, but the adapter disables that
path before forward so newly initialized physics weights do not participate in
energy computation.
