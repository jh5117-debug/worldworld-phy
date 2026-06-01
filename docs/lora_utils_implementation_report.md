# LoRA Utils Implementation Report

## Status

- Result: passed local smoke tests.
- Training: no.
- Optimizer: no.
- Optimizer step: no.
- LoRA save: no.
- Checkpoint save: no.

## Implementation

Added `cam_physgeo/dpo/lora_utils.py` with:

- `LoRALinear`: runtime wrapper around frozen `nn.Linear`.
- `inject_lora_into_modules`: replaces named `nn.Linear` modules at runtime.
- `freeze_non_lora_parameters`: freezes every parameter except names containing
  `lora_`.
- `list_lora_parameters` and `count_lora_parameters`.
- `remove_lora_from_model`: restores wrapped modules back to the original
  `nn.Linear`.

Forward formula:

`base(x) + (alpha / rank) * B(A(x))`

The base weight and bias are frozen. Only `lora_A` and `lora_B` require grad.
The wrapper is runtime-only and does not implement saving adapters.

## Why Custom Wrapper

The loaded LingBot-Fast model had no existing LoRA parameters, and this round
must not patch third-party source or save adapter weights. A small in-repo
runtime wrapper is enough for a backward-only smoke.

## Tests

- `python -m compileall -q cam_physgeo`: passed.
- `PYTHONPATH=. pytest -q tests/test_lora_utils.py`: passed, `3 passed`.
- `PYTHONPATH=. pytest -q tests/test_lora_utils.py tests/test_reward_confidence.py`:
  passed, `7 passed`.

## Limitations

- No optimizer support is added.
- No LoRA save/load path is added.
- No checkpoint writing is added.
- The wrapper only targets `nn.Linear`.
- Runtime injection is currently for smoke testing only.
