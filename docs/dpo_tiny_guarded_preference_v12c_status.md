Current Status: V12C_PRD_READY

# DPO Tiny Guarded Preference v12c Status

- v12b winner-only repair passed on filtered S_pass4.
- v12c will use only physical GPU4 through `CUDA_VISIBLE_DEVICES=4`.
- v12c will not use GPU0/1/2/3/5/6/7.
- Current task is a tiny guarded preference probe on S_pass4 only.
- Large DPO, S1/S2/S3 scale, train400, StageA, StageB, GRPO, broad-LoRA are forbidden.
- Canonical repaired ready500 is the metadata source; old ready500 is forbidden.
- If GPU4 is occupied by an unknown task, v12c training must wait or stop with `GPU4_BLOCKED`.
- Required context files missing at PRD time: none.
