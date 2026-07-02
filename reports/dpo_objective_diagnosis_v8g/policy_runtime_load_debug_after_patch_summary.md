Current Status: POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU

# v8g Policy Runtime After Patch

- Patch: Stage1 Fast loader uses local-only safetensors and low_cpu_mem_usage.
- Result: `POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU`
- Blocked stage: `14_construct_policy_model_cpu`
- Completed stages: 0_initial, 1_import_basic_python, 2_import_torch, 3_import_diffusers_transformers_peft, 4_import_lingbot_modules, 5_resolve_repo_paths, 6_resolve_config_path, 7_read_config, 8_resolve_model_weight_paths, 9_check_weight_file_sizes, 10_load_tokenizer_or_text_runtime_cpu, 11_load_t5_or_text_encoder_cpu, 12_load_vae_cpu, 13_load_policy_config_cpu
- Last timeout elapsed sec: 309.81
- Last CPU RSS GB: 2.88
- GPU allocated GB: 0.0
