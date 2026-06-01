# LingBot LoRA Target Inspection Report

## Status

- Result: partial/pass.
- Heavy `inspect_lora_targets` command was implemented but the first remote
  combined run was stopped after a long silent model-load phase.
- The final backward-only run used explicit targets derived from the previous
  camera module inventory and validated runtime injection on those targets.
- Training: no.
- Optimizer: no.
- LoRA save: no.

## Candidate Modules

From the previous camera trainable inventory and `wan/modules/model_fast.py`,
the camera/control candidates are:

- `patch_embedding_wancamctrl`
- `c2ws_hidden_states_layer1`
- `c2ws_hidden_states_layer2`
- `blocks.*.cam_injector_layer1`
- `blocks.*.cam_injector_layer2`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

These are in the Plucker/control path that injects camera scale/shift into DiT.

## Chosen Target

Tested explicit target modules:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

Reason:

- Both are late-block camera scale/shift linears.
- They are directly camera/control-related.
- They avoid the early Plucker projection path that previously retained a large
  autograd graph.
- Rank-2 LoRA adds `20,480` params per module, `40,960` total.

## Command Notes

The implemented CLI mode is:

```bash
python -m cam_physgeo.dpo.lingbot_fast_videogpa_adapter \
  --mode inspect_lora_targets \
  --rank_candidates 2 4
```

The standalone inspect run did not complete cleanly under the flaky SSH session.
The validated target information therefore comes from:

- previous module inventory;
- code-level target resolver;
- successful runtime injection during the rank-2 backward-only dry-run.

## Conclusion

The selected LoRA target is camera-aware, small enough for rank-2 backward, and
more meaningful than `tiny_subset` / `head_only`.
