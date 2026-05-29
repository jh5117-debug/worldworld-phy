# T5 Instrumented Init Report

## Actual T5 Path

Actual module path:

`local_assets/third_party/lingbot_world/wan/modules/t5.py`

`T5EncoderModel.__init__` performs:

1. `umt5_xxl(...).eval().requires_grad_(False)`
2. `torch.load(checkpoint_path, map_location="cpu")`
3. `model.load_state_dict(...)`
4. optional shard or `self.model.to(self.device)`
5. tokenizer construction

## Patch

Generated patch:

`patches/lingbot_t5_instrumentation.patch`

The patch adds `[T5_MARK]` markers around model architecture construction, `torch.load`, `load_state_dict`, device transfer, tokenizer init, and init completion. It does not alter model logic.

Remote application status:

- A backup was created during an earlier failed patch attempt: `local_assets/third_party/lingbot_world/wan/modules/t5.py.bak_20260529_134344`.
- The first patch attempt failed because the patch file was malformed.
- A corrected patch was generated and tracked, but repeated SSH reset/timeout prevented applying it reliably before this report.
- No successful third-party code change is claimed.

## Standalone Probe Markers

The standalone probe localized the same phases without modifying third-party code:

- `model_construct_start`
- `model_construct_done`
- `torch_load_start`
- `torch_load_done`
- `load_state_dict_start`
- `load_state_dict_done`
- `prompt_encode_start`
- `prompt_encode_done`

## Timing Summary

- Model architecture construction: `263-264s`
- `torch.load`: `21.8-22.4s`
- `load_state_dict`: `15.0s`
- CPU prompt encode: `109.0s`
- GPU bf16 full T5 load: `41.8s`
- GPU bf16 prompt encode: `1.4s`

## Blocker

The 120s timeout fails before checkpoint loading completes because CPU fp32 UMT5-XXL architecture construction alone takes about `264s`.

This is not an I/O issue and not a tokenizer issue.
