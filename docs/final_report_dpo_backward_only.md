# Final Report: DPO Backward-Only Dry-Run

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair backward-only plumbing with fallback `tiny_subset`.
- Gate F: no. Real DPO training remains disallowed.

## Execution

- Remote main worktree checked: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- Remote execution directory:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_energy_forward_work`
- Local branch: `physion-dpo-backward-only-dryrun`
- Base commit before this round: `c2b910feda0452d1cdf30708a5cf74e3ab215a4c`
- `local_assets` in the remote execution directory is a symlink to the main
  shared asset tree.
- No data, weights, videos, HDF5, NPY, PT, PTH, safetensors, or latents were
  moved or deleted.
- No `local_assets` content is committed.

## Prior Art

Checked VideoGPA:

- `train/loss.py`
- `train/Wan2.2-TI2V-5B/03_train.py`
- `train/dataset.py`
- `replicate.py`

Checked LingBot/Wan:

- `scripts/train_lingbot_dpo_lora.py`
- `scripts/train_lingbot_physics_predictor.py`
- `wan/image2video_fast.py`
- current LingBot adapter code.

Conclusion: VideoGPA computes DPO from policy/reference prediction-error
differences, with the reference frozen and under `no_grad`. LingBot has LoRA
training examples and camera/control module names, but this round does not run
training or save adapters.

## Trainable Scope

- Existing LoRA: none.
- Camera/control candidates: present, but very large (`4.255B` params total).
- Primary semantic scope: `camera_adapter`.
- Primary result: OOM.
- Final fallback scope: `tiny_subset`.
- Selected params:
  - `head.head.bias`
  - `head.head.weight`
- Trainable param count: `327,744`.
- Frozen param count: `23,788,523,520`.

The fallback is safe only as a gradient plumbing smoke. It is not the preferred
future training scope.

## Backward-Only Result

- Result: passed with `tiny_subset`.
- Loss: `0.6931471824645996`
- Beta: `0.1`
- `Delta_policy`: `-0.03294724225997925`
- `Delta_ref`: `-0.03294724225997925`
- Params with grad: `2`
- Params without grad: `0`
- Grad norm min: `0.0008048340096138418`
- Grad norm max: `0.04843546822667122`
- Grad norm mean: `0.02462015111814253`
- Any NaN/Inf grad: no.
- Reference params with grad: `0`.
- Optimizer: none.
- Optimizer step: none.
- Parameter update check: passed, max abs diff `0.0`.
- OOM status: primary camera scope OOMed; tiny fallback did not.

## Next Gate

Next round may consider a 1-pair optimizer-step dry-run only with explicit user
confirmation and these constraints:

- max 1 pair;
- no training loop;
- no checkpoint save;
- no LoRA save unless separately approved;
- preferably first reduce memory for camera/control trainable scope or add a
  real LoRA injection path.

Real DPO training is still no.

## Physion / TDW Generation

No generation was executed. The plan remains staged only:

1. 1 sample dry-run.
2. 10 sample smoke.
3. 50 sample validation.
4. 200 sample pilot.
5. 1k+ only after storage/runtime/user approval.

Generation should not be the immediate next step unless the user explicitly asks
for a 1-sample generation dry-run.

## Next Minimal Action

- If continuing DPO plumbing: ask user before a 1-pair optimizer-step dry-run.
- If improving trainable scope: add a real LoRA/camera-adapter injection path
  that is much smaller than full camera/control tensors.
- If preparing data: only run a 1-sample TDW generation dry-run, not scale-up.
