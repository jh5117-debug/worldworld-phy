# Final Report: Template-Diverse TDW Smoke and DPO Signal Gate Run

Date: 2026-06-04

## 1. TDW

Planned template distribution:

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Actual command outcomes:

| Template | Outcome |
|---|---|
| drop | 3 commands returned 0 |
| collision | 3 commands failed with return code 2 |
| roll | 2 commands failed with return code 2 |
| containment | 2 commands failed with return code 2 |

Validation:

| Item | Value |
|---|---|
| validation report | `local_assets/data/physion/generated_v2/reports/validation_template_diverse_10.md` |
| accepted samples | 0 |
| suitable_for_warmup | 0 |
| LingBot conversion | skipped |
| video deliverables | no new template-diverse samples added |

Exact blocker:

The non-drop templates failed because drop-only command-line args were passed to every template. The wrapper now restricts `--drop`, `--ymin`, `--ymax`, and `--dscale` to `template == "drop"`.

No second actual TDW run was started because this turn approved exactly one template-diverse 10-sample attempt.

Next TDW action: approve one more GPU0 `DISPLAY=:8` template-diverse 10-sample smoke with the fixed command builder, or configure TDW on GPU6/7.

## 2. DPO

The DPO signal sweep was run via `tmux` on GPU6/7.

Observed partial metrics:

| LR | Steps | L_DPO first -> last | Delta_policy first -> last | Preference logit first -> last |
|---:|---:|---:|---:|---:|
| 1e-5 | 3 | 0.6931471229 -> 0.6931470633 | -0.0061963499 -> -0.0061958581 | 1.311e-07 -> 1.803e-07 |

Safety:

- losses finite;
- gradients finite;
- no NaN/Inf observed;
- GPU0 was not used for DPO;
- the run was stopped after it failed to reach a second LR setting in a reasonable window.

Signal gate: **no-go**.

5-pair tiny overfit: **no-go**.

## 3. Safety

| Restriction | Status |
|---|---|
| real training | not run |
| VideoGPA `03_train.py` | not run |
| Stage1 | not run |
| LoRA save | not run |
| checkpoint save | not run |
| 50/200/1k TDW generation | not run |
| `local_assets` committed | no |
| generated HDF5/MP4/NPY/logs committed | no |

## 4. Next Actions

1. Approve a second GPU0 template-diverse 10-sample attempt after the template-specific args fix, or configure GPU6/7 TDW display.
2. Do not run 50 until a fixed template-diverse 10 passes validation and conversion.
3. Make DPO signal sweep cheaper/faster or test stronger camera-control LoRA targets.
4. Do not run 5-pair until at least two LR settings complete with a clear signal.
5. Full TDW generation and real DPO training remain blocked.

