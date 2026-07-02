Current Status: PRD_READY_NOT_RUN

# DPO Objective Diagnosis v8h Status

v8g proved direct safe `WanModelFast.from_pretrained` works on CPU and GPU7, but the integrated Stage1 helper/runtime wrapper still timed out at `14_construct_policy_model_cpu` before LoRA, move-to-GPU, runtime_ready, or cache first-row.

v8h target: expose and force a direct `safe_wan_policy_only` loader path for policy runtime/cache code, then retry policy runtime debug and one-pair minimal cache first row.

This phase will not run DPO, SDPO, Linear-DPO, Safe-linear, large DPO, StageB, GRPO, full-data StageA, or broad-LoRA.
