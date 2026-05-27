# LingBot Weight Audit

- LingBot-Base found: `True` at `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam` (149.246 GB)
- LingBot-Fast found: `True` at `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast` (69.088 GB)
- LingBot code root: `/home/nvme03/workspace/lingbot-world` import_ok=`True`

## Base
```json
{
  "exists": true,
  "files": {
    "bin": 0,
    "config_json": 2,
    "model_index_json": 0,
    "pth": 2,
    "safetensors": 16,
    "tokenizer_json": 1
  },
  "has_config": true,
  "has_fast_shards": false,
  "has_high_noise_model": true,
  "has_low_noise_model": true,
  "has_model_index": false,
  "has_t5": true,
  "has_tokenizer": true,
  "has_vae": true,
  "label": "LingBot-Base",
  "notes": [
    "legacy WanModel.from_pretrained branch layout present"
  ],
  "path": "/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam",
  "recognized_by_legacy_loader": true,
  "size_bytes": 160251929054,
  "size_gb": 149.246
}
```

## Fast
```json
{
  "exists": true,
  "files": {
    "bin": 0,
    "config_json": 1,
    "model_index_json": 0,
    "pth": 0,
    "safetensors": 16,
    "tokenizer_json": 0
  },
  "has_config": true,
  "has_fast_shards": true,
  "has_high_noise_model": false,
  "has_low_noise_model": false,
  "has_model_index": false,
  "has_t5": false,
  "has_tokenizer": false,
  "has_vae": false,
  "label": "LingBot-Fast",
  "notes": [
    "fast-style sharded checkpoint",
    "tokenizer not inside checkpoint root; may rely on companion base root"
  ],
  "path": "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast",
  "recognized_by_legacy_loader": false,
  "size_bytes": 74183049421,
  "size_gb": 69.088
}
```

## Loader Recognition

- Base is directly usable by the legacy Stage1 helper when it has `high_noise_model`, `low_noise_model`, `Wan2.1_VAE.pth`, and T5 files.
- Fast is present as a fast-style 16-shard checkpoint. It is available for Fast baseline/rollout loading through the LingBot fast runtime; if a Stage1 branch loader is requested, use Base or a branch-style adapted bundle.
- No duplicate download is needed when the Fast path above exists.
