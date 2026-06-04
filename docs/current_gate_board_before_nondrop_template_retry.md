# Current Gate Board Before Non-Drop Template Retry

Date: 2026-06-04

Scope: TDW non-drop template smoke plus short DPO signal retry. This is not training, not VideoGPA `03_train.py`, not Stage1, and not large TDW generation.

| Gate | Status | Evidence | Next Action | Can run this round? |
|---|---|---|---|---|
| TDW drop-only 10-sample | passed | `docs/final_report_tdw_10sample_warmup_smoke.md`; 10/10 accepted, all `drop` | keep as data-stack smoke, not template coverage | no rerun needed |
| TDW template-diverse plan | passed | previous plan distribution `drop:3, collision:3, roll:2, containment:2`; `bad_count=0` | verify non-drop commands | yes |
| TDW non-drop command dry-run | pending at turn start | previous blocker was drop-only args on non-drop templates | confirm no `--drop/--ymin/--ymax/--dscale` on non-drop | yes |
| TDW non-drop template smoke | pending at turn start | user approved `collision:1`, `roll:1`, `containment:1` on GPU0-bound `DISPLAY=:8` | run only after command dry-run passes | yes |
| TDW template-diverse 10 actual | blocked until non-drop passes | previous 10 failed due command args; no accepted template-diverse samples | run only if non-drop 3/3 validate | conditional |
| TDW LingBot conversion | blocked for template-diverse retry | no accepted template-diverse retry samples yet | convert accepted samples only | conditional |
| TDW video deliverables | blocked for template-diverse retry | no accepted template-diverse retry videos yet | update only after conversion | conditional |
| TDW 50 approval | no-go | template-diverse 10 has not passed | write approval request only after 10 passes | no |
| DPO signal-sensitivity | no-go at turn start | previous run reached only partial `1e-5` metrics | retry short fast sweep on GPU6/7 | yes |
| 5-pair tiny overfit | no-go | signal gate requires at least two LR settings with finite, nonzero signal | write go/no-go only | no automatic run |
| Full TDW generation | no-go | template coverage and staged 50/200 gates not passed | staged validation and approval required | no |
| Real training | no-go | signal weak; data gate incomplete | do not train | no |

