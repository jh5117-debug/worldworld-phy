Current Status:
PRD_READY_NOT_RUN

# DPO Objective Diagnosis v8g Status

Updated: 2026-07-02 21:30 CST

## Readback

v8f located the policy-only runtime blocker at `14_construct_policy_model_cpu`, specifically `WanModelFast.from_pretrained(...)`. GPU allocation stayed at approximately 0 GB, so the blocker is not CUDA forward, LoRA application, or move-to-GPU. CPU RSS climbed from roughly 0.7 GB to 20.7 GB, indicating CPU-side model construction or checkpoint shard loading.

## Current Blocker

`WanModelFast.from_pretrained(...)` is still a black box. It may hide config reading, model class construction, shard index parsing, safetensors metadata, tensor deserialization, state_dict injection, or filesystem stalls.

## v8g Objective

Split WanModelFast/diffusers `from_pretrained` and checkpoint shard loading into bounded diagnostic stages with per-shard timing and heartbeat output. This round does not run DPO, SDPO, Linear-DPO, Safe-linear, cache10 training, pair factory rollout, StageB, GRPO, full-data StageA, or broad-LoRA.

## GPU Policy

Use only H20 physical GPU4-7. Prefer GPU7 and use GPU6 only if GPU7 is unavailable. Do not use H20 GPU0-3.
