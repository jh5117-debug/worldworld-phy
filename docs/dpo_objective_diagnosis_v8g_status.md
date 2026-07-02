Current Status: POLICY_SAFE_STANDALONE_PASS_STAGE1_HELPER_STILL_TIMEOUT

# v8g Status

- v8f exact blocker was `WanModelFast.from_pretrained(...)` inside `14_construct_policy_model_cpu`.
- v8g source discovery found WanModelFast at `/home/nvme03/workspace/lingbot-world/wan/modules/model_fast.py`.
- checkpoint inventory found 16 safetensors shards totaling 69.08 GB; shard metadata and first3 tensor timing passed.
- empty/meta construction passed; state-dict prefix shard loading passed.
- standalone safe `from_pretrained` passed on CPU and GPU7 with `local_files_only=True`, `use_safetensors=True`, `low_cpu_mem_usage=True`, bf16.
- Stage1 helper was patched to those safe args, but after-patch policy runtime still timed out at `14_construct_policy_model_cpu` around 309.8 sec.
- one-pair cache first row was not attempted because policy runtime did not reach runtime_ready.
- DPO / SDPO / Linear-DPO remain blocked.
