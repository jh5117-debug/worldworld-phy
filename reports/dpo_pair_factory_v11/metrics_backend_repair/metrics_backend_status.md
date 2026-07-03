Current Status: MIXED

# Metrics Backend Repair Status

- LPIPS: AVAILABLE. Installed `lpips`; real `alex` smoke passed.
- Image FID: AVAILABLE as diagnostic package via `pytorch-fid`, but it is not FVD.
- FVD: still BLOCKED_BY_ENV_TEMPORAL_BACKBONE. `torchmetrics.video.FrechetVideoDistance` is absent; `pytorchvideo` imports but does not provide a ready FVD metric or local I3D weights. We did not fake FVD with image FID.
- VBench: PACKAGE_CLI_AVAILABLE_CONFIG_BLOCKED. `vbench` imports and CLI help works; real scoring still needs explicit dimensions, videos path, and approved local checkpoint/cache policy.

Environment caveat: installing VBench added user-site packages including `transformers==4.33.2`, which pip reports as incompatible with the existing `fastwam` expectation of `transformers==4.49.0`. Future rollout or training commands should pin or isolate their Python environment if they rely on the newer transformers version.

Artifacts:
- `backend_probe_initial.txt`
- `pip_install_lpips_fvd_vbench.log`
- `pip_install_pytorchvideo.log`
- `backend_probe_after_install.txt`
- `lpips_real_smoke.txt`
- `vbench_evaluate_help.txt`
- `metrics_backend_status.csv`
