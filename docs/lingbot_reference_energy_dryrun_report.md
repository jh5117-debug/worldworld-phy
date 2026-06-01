# LingBot Reference Energy Dry-Run Report

## Status

- Result: passed.
- Mode: `reference_energy_dryrun`
- Pair count: 1
- Training: no.
- Backward: no.
- Optimizer: no.
- LoRA save: no.

## Reference Model

- Reference checkpoint: same frozen LingBot-Fast checkpoint as policy base.
- LingBot-Base teacher: not used.
- Reward surrogate: not used.
- VideoGPA native model: not used.
- Frozen confirmed: yes.
- `torch.no_grad()` confirmed: yes.
- Policy/reference same weights: yes.

## Energy

- Target: `flow_velocity_noise_minus_x0`
- Sigma for timestep: `0.17600001394748688`
- Target evidence: LingBot `sample_flow_batch` and VideoGPA Wan2.2 flow matching path.
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_ref_loser_minus_winner`: `-0.03294724225997925`
- Values finite: yes.

## Memory

- `CUDA_VISIBLE_DEVICES`: `6,7`
- Actual model device: first visible CUDA device, i.e. physical GPU 6.
- Peak allocated bytes: `54436894208`
- Reserved bytes: `56612618240`
- GPU 6/7 returned to idle after completion.

## Notes

Reference energy numerically matches policy energy because this dry-run uses the
same frozen checkpoint for policy and reference and no LoRA/policy delta has
been introduced. This is expected and only validates the reference forward path.

The Fast checkpoint still emits warnings about optional `physics_*` adapter
weights being newly initialized. The adapter disables that optional path before
forward; the dry-run does not train or use those random modules.

## Gate

Reference energy is now passed for 1-pair no-backward smoke. Scalar DPO loss
dry-run is allowed, but real DPO training is still not allowed.
