# Current Gate Board Before Accelerated Run

Generated before the accelerated TDW/DPO smoke pass on branch `physion-accelerated-gates-tdw-dpo`.

| Gate | Status | Evidence | Next Action | Can run this round? |
|---|---|---|---|---|
| Git remote integrity | passed | `origin` must be `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`; previous wrong `world_model_phys.git` was fixed. | Re-check before push. | yes |
| TDW warmup_mild plan | passed | `warmup_mild` camera set allows only `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`; dry-run `bad_count=0`. | Re-check plan before generation. | yes |
| TDW 1-sample actual | blocked before this run | Prior GPU0-approved attempt produced no HDF5/MP4 because wrapper path and JSON boolean bugs stopped before TDW scene generation. | Rerun exactly one `warmup_mild` sample on approved `DISPLAY=:8` after fixes. | yes, exactly 1 sample |
| TDW validation | pending | No generated HDF5/MP4 existed from the prior failed attempt. | Run validator only if 1-sample produces files. | conditional |
| TDW 10-sample smoke | pending | Requires 1-sample success, completeness, mild camera, visible foreground, conversion pass, and GPU approval if using GPU0. | If GPU0 is required, write approval request instead of running. | conditional |
| TDW 50-sample validation | not allowed by default | Requires 10-sample success and no large GPU use, or explicit user approval. | Do not run unless conditions are met. | no by default |
| TDW LingBot conversion | pending | Requires accepted TDW v2 sample. | Convert only accepted samples with `use_action=false` and dummy action. | conditional |
| TDW video deliverables | partial | Existing gallery/index includes older Physion-style TDW stress samples and LingBot/camera ablation assets. | Add new TDW v2 sample only if generated. | conditional |
| DPO signal-sensitivity | weak | Previous probes showed LoRA is active when scaled, but default rank-2 energy movement was about `5.960e-08`; full sweep was runtime-blocked. | Run fast fixed-noise LR sweep with reused policy/reference loads. | yes |
| 5-pair tiny overfit | skipped | Previous signal gate was weak; 5-pair was intentionally not run. | Only run if fast sweep gives clear nonzero stable signal. | conditional |
| Real DPO training | no | Engineering smoke gates do not authorize training. | Keep disabled. | no |
| Full TDW generation | no | Requires staged 1/10/50 validation and user approval for large jobs. | Prepare readiness report only. | no |

Constraints for this run:

- No real training, no VideoGPA `03_train.py`, no Stage1, no LingBot rollout, no reward calibration.
- No LoRA/checkpoint save.
- No `local_assets` commit.
- GPU0-bound `DISPLAY=:8` may be used only for exactly one TDW `warmup_mild` sample in this run.
- DPO signal diagnostics must use only GPUs 6/7 via `CUDA_VISIBLE_DEVICES=6,7`.
