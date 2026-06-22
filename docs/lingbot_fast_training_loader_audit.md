# LingBot-Fast Training Loader Audit

```json
{
  "model_family": "lingbot_world_fast",
  "policy_checkpoint_realpath": "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast",
  "shared_assets_realpath": "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam",
  "state_dict_index": "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast/diffusion_pytorch_model.safetensors.index.json",
  "shard_count": 16,
  "first_shard_sha16": "6db4d3b1f7ea8fd6",
  "last_shard_sha16": "741e26f28a545ab7",
  "model_class": "WanModelFast",
  "total_parameters": 18647224384,
  "trainable_parameters_after_lora": 102891520,
  "load_seconds": 473.08216309547424,
  "cuda_visible_devices": "7",
  "base_branch_in_policy_path": false,
  "fast_root_name": "lingbot_world_fast"
}
```

Conclusion: policy load used WanModelFast from lingbot_world_fast; Base low/high branch policy path was not used. Shared assets remain used for VAE/T5/tokenizer.
