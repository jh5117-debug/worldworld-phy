Current Status:
BLACKBOX_STAGE_IDENTIFIED

# v8f Black-Box Loader Split Note

- Blocked stage: `14_construct_policy_model_cpu`
- Outer call: `helper.WanModelFast.from_pretrained(...)`
- WanModelFast class source: `/home/nvme03/workspace/lingbot-world/wan/modules/model_fast.py`
- Inherited loader path observed by introspection: `/usr/local/lib/python3.10/dist-packages/huggingface_hub/utils/_validators.py` wrapping diffusers `ModelMixin.from_pretrained`
- Runtime behavior: CPU RSS climbed from ~0.7 GB to ~20.7 GB over ~186 seconds while GPU allocation stayed at 0 GB.

The blocked call combines model construction and checkpoint/shard loading. v8f did not start DPO training. The next split should instrument per-shard loading inside the diffusers/LingBot `from_pretrained` path or add a bounded local shard loader with progress rows.
