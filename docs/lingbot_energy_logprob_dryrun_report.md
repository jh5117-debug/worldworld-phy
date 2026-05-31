# LingBot Energy / Logprob Dry-Run Report

## Result

- Status: `not_implemented`.
- This is an expected safe stop, not a fake success.
- Batch summary exists: yes.
- No backward: true.
- No optimizer: true.
- Energy/logprob values: none.

## Forward Path Inspection

The adapter inspected LingBot modules and found:

- `wan.image2video_fast`: `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- Candidate members: `FlowUniPCMultistepScheduler`, `sp_attn_forward_causal`, `sp_dit_forward_causal`
- `wan.modules.model`: imported, but no wired training-loss/velocity target was selected by the adapter.
- `wan.modules.vae`: missing as a module name; actual VAE load uses `wan.modules.vae2_1`.

## Blocker

`compute_dpo_energy_or_logprob` remains `NotImplementedError` because the adapter has not identified and wired a real LingBot denoising / velocity / flow-matching training target.

The next implementation must find the exact LingBot-Fast model forward contract for:

- latent input layout;
- noisy latent and timestep schedule;
- velocity/noise target;
- camera/control tensor injection;
- frozen reference model forward;
- policy model forward;
- no-fake scalar energy from prediction error.

## Gate Impact

- It is not yet allowed to run a 1-pair DPO loss scalar dry-run.
- Real DPO training remains disallowed.

