# Final Report: Template-Diverse TDW Gate and DPO Signal Sweep

Date: 2026-06-03

## 1. Gate Board Final

| Gate | Status | Notes |
|---|---|---|
| TDW template coverage | code fixed; dry-run passed | plan distribution `drop:3`, `collision:3`, `roll:2`, `containment:2` |
| TDW 10 template-diverse actual | not run | requires new GPU0 `DISPLAY=:8` approval |
| TDW 50 readiness | no-go | waits for template-diverse 10 actual |
| DPO signal | no-go / incomplete | no usable new multi-LR summary |
| 5-pair tiny overfit | no-go | signal gate not passed |
| Full TDW generation | no-go | staged validation incomplete |
| Real training | no | still not allowed |

## 2. TDW

Previous TDW status:

- 1-sample `warmup_mild` passed.
- 10-sample `warmup_mild` passed HDF5 validation and LingBot conversion.
- The previous 10 samples were all `drop`, so template coverage was incomplete.

This turn:

- Added exact `--template_counts`.
- Added manifest-driven per-trial generation.
- Added manifest filtering for validation and conversion.
- Verified dry-run template distribution:

| Template | Planned Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Stress/reobserve variants in the template-diverse plan: `0`.

Actual generation was not run because the only known TDW display is GPU0-bound `DISPLAY=:8`, and the current prompt did not approve GPU0 for this new template-diverse 10-sample run.

Approval request: `docs/gpu_usage_approval_request_tdw_template_diverse_10.md`.

## 3. DPO

The DPO chain remains validated up to:

- scalar DPO loss;
- LoRA backward-only;
- 1-pair optimizer-step dry-run;
- 1-pair 5-step mini-loop.

The signal gate remains weak/incomplete:

- historical default rank-2 energy movement: about `5.960e-08`;
- historical preference logit movement: about `2.831e-08`;
- no complete new multi-LR fast-sweep summary was produced this turn.

5-pair tiny overfit was not run. Go/no-go: `docs/5pair_tiny_overfit_go_nogo.md`.

## 4. Safety

| Safety Item | Status |
|---|---|
| Real training | not run |
| VideoGPA `03_train.py` | not run |
| Stage1 | not run |
| LingBot rollout | not run |
| Reward calibration | not run |
| LoRA save | not run |
| Checkpoint save | not run |
| 50/200/1k TDW generation | not run |
| `local_assets` committed | no |
| HDF5/MP4/NPY/PT/weights/latents committed | no |

## 5. Next Actions

1. Approve GPU0 `DISPLAY=:8` for exactly one template-diverse 10-sample TDW smoke, or configure a GPU6/7 TDW display.
2. Run template-diverse 10 actual and validate per-template success.
3. Convert accepted template-diverse samples to LingBot cam-only inputs.
4. Only then request 50-sample validation approval.
5. For DPO, fix signal runner robustness or try a stronger camera-control LoRA scope before 5-pair.
6. Full TDW generation and real DPO training remain disallowed until staged gates pass and the user approves.

