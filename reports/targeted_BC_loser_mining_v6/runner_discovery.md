# Targeted B/C v6 Runner Discovery

Current Status: RUNNER_FOUND

## Deterministic Discovery

Known paths checked:

- `cam_physgeo/eval/run_v2v5_inference.py`: FOUND
- `cam_physgeo/eval/v2v5_generation_wrapper.py`: FOUND
- `scripts/launch_v2v5_inference.sh`: MISSING

The runner CLI was inspected from source instead of relying on a broad repository search or long-running `--help` import.

Important arguments:

- `--manifest`
- `--model`
- `--adapter_path`
- `--output_root`
- `--repo_root`
- `--ckpt_dir`
- `--height`, `--width`, `--num_frames`
- `--prefix_len`, `--prediction_start_frame`
- `--seed`
- `--max_samples`
- `--bf16`
- `--t5_cpu`

## Smoke Manifest

Using `reports/targeted_BC_loser_mining_v6/smoke_condition_manifest.jsonl`, selected from `manifests/screen16_v2v5.jsonl`, because quant benchmark rows do not include a direct `prefix_video_path` for this runner.

## Safety

No broad runner discovery is used. No training code is invoked.
