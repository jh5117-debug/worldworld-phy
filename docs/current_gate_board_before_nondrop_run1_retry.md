# Current Gate Board Before Non-Drop `--run 1` Retry

Date: 2026-06-04

| Gate | Status | Evidence | Next Action |
|---|---|---|---|
| drop-only 10-sample | passed | 10/10 accepted in earlier `warmup_mild` smoke; all were `drop` | keep as data-stack smoke only |
| non-drop dry-run | passed previously | non-drop templates no longer receive `--drop`, `--ymin`, `--ymax`, `--dscale` | verify `--run 1` is now present |
| non-drop actual with missing `--run` | failed | command returned 0 but validation was 0/3; no HDF5 written | fixed by adding `--run 1` |
| `--run 1` fix | implemented | `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py` passes `--run 1` | rerun non-drop 3 only |
| non-drop retry | approved this round | user approved GPU0-bound `DISPLAY=:8` for `collision:1`, `roll:1`, `containment:1` | run and validate; stop if not 3/3 |
| template-diverse 10 | conditional | planned `drop:3`, `collision:3`, `roll:2`, `containment:2` | run only if non-drop retry validates 3/3 |
| template-diverse conversion | conditional | requires accepted template-diverse samples | skip if template-diverse 10 does not run/pass |
| 50 readiness | no-go until template-diverse 10 passes | no approved 50 run | write approval request only after 10 passes |
| DPO signal | separate no-go | previous fast retry did not complete usable two-LR summary | not run this round |
| 5-pair | no-go | DPO signal gate not passed | not run |
| full TDW generation | no-go | template-diverse 10/50 not passed | staged approval required |
| real training | no-go | data and DPO gates incomplete | do not train |

