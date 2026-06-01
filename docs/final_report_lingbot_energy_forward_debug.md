# Final Report: LingBot Energy Forward Debug

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair plumbing smoke: latent encode, condition encode, batch shape, real forward, and policy energy all passed.
- Gate F: no. DPO training is still not allowed.

## Prior-Art Review

Reviewed local LingBot/Wan files:

- `wan/image2video_fast.py`
- `wan/modules/model_fast.py`
- `scripts/train_lingbot_physics_predictor.py`

Reviewed VideoGPA files:

- `train/loss.py`
- `train/Wan2.2-TI2V-5B/03_train.py`

Existing DPO prior art uses prediction-error energies. The real LingBot target
is flow velocity `noise - x0`; this is backed by LingBot local training code
and LingBot inference conversion comments.

## Forward Path

- Policy runtime: `WanI2VFast`
- Policy DiT: `WanModelFast`
- Forward signature: `(x, t, context, seq_len, y, dit_cond_dict, kv_cache, crossattn_cache, current_start, max_attention_size)`
- Scheduler: `FlowUniPCMultistepScheduler`
- Latent convention: `[C, F, H, W]`
- Smoke latent shape: `[16, 2, 60, 104]`
- Camera condition: `dit_cond_dict["c2ws_plucker_emb"]`
- Control tensor shape: `[1, 384, 2, 60, 104]`
- Image condition shape: `[20, 2, 60, 104]`
- Text context shape: `[47, 4096]`
- `use_action=false`, dummy action norm `0.0`

## Policy / Reference

- Policy load: passed.
- Model class: `WanModelFast`
- Device: `cuda:0` under `CUDA_VISIBLE_DEVICES=6,7`
- Dtype: `bfloat16`
- Parameters: `23,788,851,264`
- Trainable parameters: `0`
- Peak memory: about `54.44 GB` during forward/energy smoke.
- Optional physics adapter path: disabled for dry-run.
- Reference model: deferred, not faked.

## Model Forward

- Winner forward: passed.
- Loser forward: passed.
- Prediction shape: `[16, 2, 60, 104]`
- Prediction dtype: `float32`
- Prediction NaN/Inf: none.
- Target shape: `[16, 2, 60, 104]`
- Sigma for timestep `176`: `0.17600001394748688`

## Energy / Logprob

- Status: passed for policy energy dry-run.
- Target: `flow_velocity_noise_minus_x0`.
- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `Delta_policy_loser_minus_winner`: `-0.03294724225997925`
- Energies finite: yes.
- Reference energies: deferred.
- DPO scalar loss: not computed.
- Backward: not run.
- Optimizer: not run.
- LoRA save: not run.

The loser energy being lower than winner on this single pair is not interpreted
as a DPO result. It is only a proof that real policy energy can be computed.
Preference comparison still requires a real frozen reference and an explicit
scalar-loss dry-run.

## Next Round Permission

Next round may do a 1-pair scalar DPO loss dry-run only after user confirmation
and only with these constraints:

- real frozen reference energy, not deferred;
- max 1 pair;
- no training loop;
- no optimizer;
- no checkpoint or LoRA save;
- no real DPO training.

Real DPO training remains disallowed.

## Next Minimal Action

Implement or load a real frozen reference forward under memory constraints,
then compute a scalar DPO formula without backward. Do not jump to training.
