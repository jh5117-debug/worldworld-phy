# LingBot Energy / Logprob Dry-Run V2 Report

## Result

- Status: passed for policy energy dry-run.
- Real LingBot forward found: yes.
- Real target found: yes.
- Target type: `flow_velocity_noise_minus_x0`.
- Energy definition used: `MSE(pred, noise - x0)`.
- Backward: not run.
- Optimizer: not run.
- DPO loss: not computed.

## Evidence For Target

- LingBot `scripts/train_lingbot_physics_predictor.py::sample_flow_batch`
  constructs `z_t` and `target = noise - x0`.
- LingBot `wan/image2video_fast.py::_convert_flow_pred_to_x0` documents model
  prediction as `noise - x0`.
- VideoGPA `Wan2.2-TI2V-5B/03_train.py` uses the same velocity target for
  winner/loser preference training.

## Energy Values

- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `Delta_policy_loser_minus_winner`: `-0.03294724225997925`
- Finite check: passed.

These values are raw policy prediction-error energies for one smoke pair. They
are not DPO preference scores because the frozen reference model was deferred
and no DPO scalar loss was computed.

## Forward Details

- Policy model: `WanModelFast` through `WanI2VFast`.
- Scheduler: `FlowUniPCMultistepScheduler`.
- Timestep: `176`.
- Sigma: `0.17600001394748688`.
- Winner / loser pred shape: `[16, 2, 60, 104]`.
- Winner / loser target shape: `[16, 2, 60, 104]`.
- Camera/control tensor shape: `[1, 384, 2, 60, 104]`.
- Image condition shape: `[20, 2, 60, 104]`.
- Text context shape: `[47, 4096]`.
- `use_action=false`; dummy action norm remains `0.0`.
- Optional physics adapter path disabled: `physics_adapter_enabled=false`.
- Peak CUDA allocation observed: about `54.44 GB`.

## Reference Status

Reference is deferred. It should be a frozen same-weight LingBot-Fast model in
the next scalar-loss dry-run, or a memory-saving shared/reference-forward plan
must be designed. No reference energy was faked.

## Gate Impact

Gate E now passes the real-forward policy-energy smoke. Gate F remains closed:
real DPO training is still not allowed.
