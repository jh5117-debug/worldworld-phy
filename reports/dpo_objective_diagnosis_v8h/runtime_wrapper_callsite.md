Current Status: CALLSITE_IDENTIFIED_AND_PATCHED

# v8h Runtime Wrapper Callsite

- Primary debug callsite: cam_physgeo/dpo/policy_runtime_load_debug.py stage 14_construct_policy_model_cpu.
- Cache callsite: cam_physgeo/dpo/winner_anchor_cache_builder.py build_cache.
- Energy backend callsite: cam_physgeo/dpo/lingbot_fast_energy.py LingBotFastDpoEnergy.
- v8h adds loader_mode=safe_wan_policy_only and direct safe Wan policy loading with local_files_only/use_safetensors/low_cpu_mem_usage.
- Runtime debug skips T5/VAE with --skip_text true --skip_vae true.
- Cache builder keeps VAE/T5 available because cache prep needs them, but policy load uses safe loader.
- No distributed init, reference, loser, DPO, or optimizer is added.
