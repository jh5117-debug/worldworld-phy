Current Status: V12C_GPU4_BLOCKED

# DPO Tiny Guarded Preference v12c Status

- PRD is ready and pushed.
- v12c setup completed: S_pass4 is ready and warm-start step20 LoRA is loadable.
- LocalDPO mask audit completed: 3/4 S_pass pairs have spatial/time local mask metadata.
- v12c implementation and direct smoke tests are ready.
- Tiny guarded preference training has NOT started.
- Reason: physical GPU4 is occupied by non-project `eval_libero_single.py gpu_id=4` processes across multiple polls.
- Per hard rule, v12c cannot use GPU0/1/2/3/5/6/7 as fallback and cannot kill unknown tasks.
- Decision: `V12C_GPU4_BLOCKED` until GPU4 is free.
