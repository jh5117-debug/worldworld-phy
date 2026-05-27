# LingBot Loader Report: Physion

Known local checkpoints:

- LingBot-Base: `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam`, about 149.246 GB. Branch-style high/low noise model layout with VAE/T5 was recognized in the previous audit and can serve as teacher/baseline.
- LingBot-Fast: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`, about 69.088 GB. Fast-style sharded checkpoint exists and should not be downloaded again.
- LingBot code root: `/home/nvme03/workspace/lingbot-world`.

The Physion pipeline supports `model_type=base|fast`, no-action conditioning, and dry-run path checks. Full smoke inference remains capped to one tiny sample when explicitly requested.
