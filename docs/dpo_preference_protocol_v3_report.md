# DPO Preference Protocol v3 Report

Current Status: MIXED_TYPEA_READY_TYPEB_BLOCKED
Updated: 2026-06-29 15:38:49

## Summary

- Manifest: `manifests/dpo_preference_protocol_v3_pairs.jsonl`
- Total valid pairs: 34
- Type A local corruption: 34
- Type B rollout loser: 0
- Type C: 0
- LocalDPO spatial mask v2: PASS, 34 usable spatial+time masks.

## Decision

Protocol v3 is ready for LocalDPO-style / TypeA-only engineering smoke. It is not ready as a rollout-based Type B protocol because candidate-generator v2 has not run and Protocol v2 rejected every Type B rollout loser for blur/sharpness quality.

## Next

Wait for GPU capacity before running candidate-generator v2. If Type B remains blocked, use TypeA-only for tiny DPO smoke and do not scale.
