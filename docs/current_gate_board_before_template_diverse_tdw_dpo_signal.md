# Gate Board Before Template-Diverse TDW / DPO Signal Run

Date: 2026-06-03

Worktree used for code/docs: `/tmp/worldworld_phy_push_tdw_prd`

Base branch: `physion-tdw-10sample-warmup-smoke`

Base commit: `24a9da865f2d5bd5920568ca91708981c32bd823`

Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

No training, DPO training, VideoGPA `03_train.py`, Stage1, LingBot rollout, reward calibration, 50/200/1k TDW generation, LoRA save, or checkpoint save was started for this gate board.

| Gate | Status | Evidence | Next Action | Can run this round? |
|---|---|---|---|---|
| Git remote integrity | passed | `origin` is `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git` | keep pushing only to this repo | yes |
| TDW warmup_mild camera set | passed | allowed variants are orbit/strafe/dolly mild; banned stress/reobserve variants remain filtered | keep bad_count check before generation | yes |
| TDW 1-sample actual | passed | `drop + orbit_left_12`, visibility 1.0, max invisible 0, HDF5 complete | keep as known-good smoke | no need |
| TDW 10-sample actual | passed, but incomplete coverage | 10/10 valid, 10/10 converted, but all were `drop` | fix template coverage before 50 | yes, code/plan only unless GPU approval |
| TDW template diversity | failed before this run | actual distribution was `drop:10` | force per-trial template execution from manifest | yes |
| TDW 50-sample validation | blocked | template coverage missing; GPU0 approval not granted for 50 | write approval only after template-diverse 10 passes | no |
| TDW LingBot conversion | passed for previous 10 | target.mp4 probe passed 10/10, `use_action=false`, dummy action zero | extend manifest filtering for template-diverse samples | yes |
| TDW video deliverables | partial/pass | existing 1/10 drop-only samples indexed; template-diverse samples absent | update after actual template-diverse run | no actual update without generation |
| DPO signal-sensitivity | no-go | previous fast sweep did not produce usable LR summary; signal remains weak | rerun only on GPU6/7 when stable | attempted/recorded only |
| 5-pair tiny overfit | no-go | signal gate not passed | do not run | no |
| Full TDW generation | no-go | needs template-diverse 10, 50 validation, approval | staged only | no |
| Real DPO training | no | signal weak; 5-pair no-go; no training approval | do not train | no |

