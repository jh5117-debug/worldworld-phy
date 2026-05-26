# LingBot Weight Audit

- LingBot-Base found: `true`
- LingBot-Base path: `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam`
- LingBot-Base size: `149.246 GB`
- LingBot-Base loader status: legacy branch layout recognized (`high_noise_model`, `low_noise_model`, `Wan2.1_VAE.pth`, T5/tokenizer present).

- LingBot-Fast found: `true`
- LingBot-Fast path: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`
- LingBot-Fast size: `69.088 GB`
- LingBot-Fast files: `config.json` plus 16 `model-*-of-00016.safetensors` shards.
- LingBot-Fast loader status: fast-style sharded checkpoint exists; it is not the same branch-folder layout as the legacy Stage1 `WanModel.from_pretrained` helper, so Stage1 warm-up currently uses LingBot-Base/branch bundles and Fast is used for Fast runtime rollout/policy initialization.

LingBot code root:

- `/home/nvme03/workspace/lingbot-world`
- `wan/modules/model.py` exists.
- Legacy import check passed during dry-run audit.

Conclusion: LingBot-Fast is already downloaded on H20. No duplicate download is needed.
