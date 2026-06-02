# Current State Before DPO Signal Sensitivity

## Source State

- Previous branch: `physion-dpo-fixed-noise-diagnostic`.
- Fixed-noise diagnostic commit: `8582cad98bede32ad33319c1adf3a74ba23768ab`.
- Correct GitHub repository for user-visible pushes:
  `jh5117-debug/worldworld-phy`.
- Current local implementation branch:
  `physion-dpo-signal-sensitivity`.

## Fixed-Noise Diagnostic Result

- Status: passed for stability and parameter-safety.
- Pair count: `1`.
- Steps: `10 / 10`.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- LoRA targets:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA rank/alpha: `2 / 4.0`.
- Trainable LoRA params: `40,960`.
- Optimizer: `AdamW`, lr `1e-5`.

## Metrics

- `loss_first`: `0.6931471229`.
- `loss_last`: `0.6931471825`.
- `loss_delta`: `+5.96e-08`.
- `Delta_policy`: `-0.0061962008 -> -0.0061972886`.
- `Delta_ref`: `-0.0061976612`.
- LoRA params changed: yes, final max diff about `1.006e-4`.
- Base params changed: no, max diff `0.0`.
- Reference params changed: no, max diff `0.0`.
- LoRA gradients finite: yes.
- Base/reference gradients: `0`.
- OOM: no.
- Peak allocation: about `50.77 GiB`.
- `restore_after_loop`: passed.

## Interpretation

The previous run proves that fixed-noise DPO plumbing is safe, but the learning
signal is weak. Loss stays near `log(2)`, LoRA parameters move, and energy/logit
changes are extremely small. Plausible causes:

- lr `1e-5` is too conservative for a visible 1-pair diagnostic;
- last-block camera shift/scale LoRA is too narrow or too late;
- LoRA forward contribution is very small at rank 2 / alpha 4;
- the pair's reward margin is not strongly reflected in this energy target;
- sign/target should be rechecked if stronger settings move loss the wrong way.

## Current Allowed Actions

Allowed this round:

- 1-pair no-backward LoRA functional influence probe;
- 1-pair fixed-noise LR sensitivity sweep;
- optional 1-pair fixed-noise camera-scope sensitivity sweep;
- optional no-step beta/sign logging;
- docs and code push.

Still forbidden:

- real training;
- VideoGPA `03_train.py`;
- multi-pair DPO;
- Stage1;
- rollout generation;
- reward calibration;
- TDW/Physion generation;
- LoRA/checkpoint save;
- committing `local_assets`.

The run should not jump to 5-pair yet because the single-pair fixed-noise signal
is not clearly measurable.
