# Final Report: Reference Energy and DPO Scalar Dry-Run

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair no-backward plumbing: pair metadata, LingBot
  latent encode, condition encode, batch shape, policy energy, reference
  energy, and scalar DPO loss all pass.
- Gate F: no. Real DPO training remains disallowed.

## Prior Art

Checked LingBot/Wan files:

- `wan/image2video_fast.py`
- `wan/modules/model_fast.py`
- `scripts/train_lingbot_physics_predictor.py`

Checked VideoGPA files:

- `train/loss.py`
- `train/Wan2.2-TI2V-5B/03_train.py`
- `train/dataset.py`

External primary references checked:

- https://github.com/Hongyang-Du/VideoGPA
- https://github.com/CIntellifusion/VideoDPO
- https://github.com/Wan-Video/Wan2.1
- https://github.com/cogtoolslab/physics-benchmarking-neurips2021
- https://github.com/threedworld-mit/tdw

Conclusion: use LingBot/Wan flow matching target `noise - x0`; reference energy
uses the same prediction-error formula as policy energy, under a frozen
same-checkpoint reference. VideoGPA's DPO loss compares policy improvement over
reference improvement.

## Reference Energy

- Status: passed.
- Reference checkpoint: same frozen LingBot-Fast checkpoint as policy base.
- LingBot-Base teacher: not used.
- Frozen confirmed: yes.
- `torch.no_grad()` confirmed: yes.
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_ref`: `-0.03294724225997925`
- Finite check: passed.
- Peak allocated GPU memory: `54436894208` bytes.
- GPU use: `CUDA_VISIBLE_DEVICES=6,7`, actual model on physical GPU 6.

## DPO Scalar Loss

- Status: passed.
- Beta: `0.1`
- `E_policy_winner`: `0.8652140498161316`
- `E_policy_loser`: `0.8322668075561523`
- `E_ref_winner`: `0.8652140498161316`
- `E_ref_loser`: `0.8322668075561523`
- `Delta_policy`: `-0.03294724225997925`
- `Delta_ref`: `-0.03294724225997925`
- `L_DPO`: `0.6931471824645996`
- Loss finite: yes.
- Backward: no.
- Optimizer: no.
- LoRA save: no.

Sign convention: lower energy means higher likelihood under the denoising-error
proxy. `Delta = E_loser - E_winner`; positive means the model assigns lower
energy to the winner. The scalar formula is
`-log sigmoid(beta * (Delta_policy - Delta_ref))`.

Because policy and reference are identical in this smoke, `Delta_policy` equals
`Delta_ref`, so the scalar is `log(2)`. This is expected and confirms plumbing,
not learning.

## Physion / TDW Generation Plan

Physion official code and TDW generation sources are present locally. The
official Physion repo assumes stimuli are generated with `tdw_physics`; our
moving-camera data comes from project-specific wrappers layered on
TDW/tdw_physics outputs.

No data generation was run. Large generation can happen only after user
approval and staged validation:

1. 1 sample dry-run.
2. 10 sample smoke.
3. 50 sample validation.
4. 200 sample pilot.
5. 1k+ batch after storage/runtime approval.

Future outputs should use `local_assets/data/physion/generated_v2/` and must
not overwrite migrated data.

## Next Round

May do a 1-pair backward-only dry-run only after explicit user confirmation,
with:

- max 1 pair;
- real policy/reference energies;
- no optimizer;
- no training loop;
- no checkpoint or LoRA save.

Real DPO training remains no. If the next goal is data generation, start only
with a 1-sample TDW generation dry-run.
