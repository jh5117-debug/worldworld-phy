# PhysEditWorld Prompt-Gravity Policy Audit

Decision: `PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS`

## Policy

- First version uses gravity in text prompt only.
- No gravity MLP, embedding, encoder, projector, or continuous gravity conditioning is allowed.
- Prompt must include a `gravity: {value}g` token and must not leak future outcomes.

## Status Counts

- `PASS`: 10

## Checks

- `prompt_sample`: `PASS`
  - evidence: `cam_physgeo/data/prompt_gravity.py`
  - detail: value=0.25; expected_token=gravity: 0.25g; errors=[]; prompt='A first-person interactive world rollout.\nThe character follows the given action sequence and camera trajectory.\nThe scene is rendered under gravity: 0.25g.'
- `prompt_sample`: `PASS`
  - evidence: `cam_physgeo/data/prompt_gravity.py`
  - detail: value=1.0; expected_token=gravity: 1.0g; errors=[]; prompt='A first-person interactive world rollout.\nThe character follows the given action sequence and camera trajectory.\nThe scene is rendered under gravity: 1.0g.'
- `prompt_sample`: `PASS`
  - evidence: `cam_physgeo/data/prompt_gravity.py`
  - detail: value=4.0; expected_token=gravity: 4.0g; errors=[]; prompt='A first-person interactive world rollout.\nThe character follows the given action sequence and camera trajectory.\nThe scene is rendered under gravity: 4.0g.'
- `future_leak_detector`: `PASS`
  - evidence: `cam_physgeo/data/prompt_gravity.py`
  - detail: errors=['future_answer_leak']
- `no_gravity_mlp_or_embedding`: `PASS`
  - evidence: `cam_physgeo/data/prompt_gravity.py`
  - detail: no forbidden gravity conditioning symbols
- `no_gravity_mlp_or_embedding`: `PASS`
  - evidence: `cam_physgeo/data/physeditworld_to_lingbot.py`
  - detail: no forbidden gravity conditioning symbols
- `conversion_writes_prompt_only_metadata`: `PASS`
  - evidence: `cam_physgeo/data/physeditworld_to_lingbot.py`
  - detail: conversion records gravity_condition_type=prompt_only
- `no_gravity_mlp_or_embedding`: `PASS`
  - evidence: `cam_physgeo/data/lingbot_condition_schema.py`
  - detail: no forbidden gravity conditioning symbols
- `no_gravity_mlp_or_embedding`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: no forbidden gravity conditioning symbols
- `warmup_config_prompt_only`: `PASS`
  - evidence: `configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml`
  - detail: warmup config keeps gravity: prompt_only

## Safety

This audit is CPU/IO only. It does not use GPUs, train, rollout, copy data, delete files, or inspect local_assets.
