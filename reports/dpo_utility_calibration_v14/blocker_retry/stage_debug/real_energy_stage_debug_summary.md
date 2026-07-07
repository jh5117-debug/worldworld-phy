# v14 Real-Energy Stage Debug Summary

Generated: `2026-07-08T04:01:06`

Decision: `REAL_ENERGY_STAGE_DEBUG_TIMEOUT_ENCODE_WINNER_PROBE`

## Stage Result

- `1_load_config`: PASS in about 0.06s.
- `2_load_dataset`: PASS.
- `3_normalize_protocol`: PASS.
- `4_init_energy_runtime`: PASS but slow, about 557.6s.
- `5_decode_example`: PASS but slow, about 68.1s.
- `6_move_winner_video_to_device`: PASS, about 0.64s.
- `7_encode_winner_probe`: started and heartbeated until timeout; no `stage_done` before the 900s process timeout.

## Resource Evidence

- Last stage: `7_encode_winner_probe`.
- Last event: `heartbeat`.
- Last elapsed seconds: `871.3553779125214`.
- Last CPU RSS GB: `49.53215026855469`.
- Last GPU allocated GB: `37.587993088`.

## Interpretation

The repaired one-pair real-energy path now gets past schema adaptation, Python environment conflict, model shard loading, dataset decode, and device transfer. The current exact blocker is the VAE encode path for the winner video (`energy._encode_video(winner_video)`) under the LingBot runtime. It does not complete before the 900 second bound.

This does not change the DPO decision: `DPO_RECIPE_NOT_FOUND_V14`; S16/S32/train400 remain blocked.

## Safe Next Step

Do not run more DPO training. Add a cached/precomputed latent path or a minimal VAE-only encode smoke with lower resolution/window to prove the VAE encode can finish, then reconnect it to real-energy calibration.
