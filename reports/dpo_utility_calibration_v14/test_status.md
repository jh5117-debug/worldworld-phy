# v14 Test Status

- `python3 -m compileall cam_physgeo src tests`: PASS on 2026-07-08 after the v14 visual-gate report updates.
- `pytest -q tests/test_v14_pair_inventory.py tests/test_utility_calibration_v14.py tests/test_beta_loss_response_v14.py tests/test_latent_relation_monitor_v14.py tests/test_dpo_objective_search_v14.py tests/test_gpu_scheduler_v14.py tests/test_dpo_same_noise_timestep.py tests/test_reference_frozen.py`: NOT RUN because `pytest` is not available in the active H20 shell (`bash: pytest: command not found`).
- No pytest PASS is claimed.
- Direct import smoke for v14 modules: PASS (`reports/dpo_utility_calibration_v14/direct_import_smoke_v14.md`).


## v14 DINOv2 Latent Monitor Test Update (2026-07-07T22:20:16Z)

- `python3 -m compileall cam_physgeo src tests`: PASS.
- Direct smoke for `tests/test_latent_relation_monitor_v14.py`: PASS for audit no-fake-values, code-only blocker, local weight detection, DINOv2 qkv mapping, and future-frame sampling.
- `pytest -q tests/test_latent_relation_monitor_v14.py`: NOT RUN because `pytest` is unavailable in the active H20 shell (`exit 127`). No pytest PASS is claimed.
- DINOv2 frame smoke: `LATENT_MONITOR_DINO_FRAME_SMOKE_PASS` with 4/4 ok rows.
