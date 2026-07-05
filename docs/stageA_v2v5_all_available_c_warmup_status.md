# StageA V2V-5 All-Available C-Scope Warmup Status

Date: 2026-07-05
Branch: research/quant-small-lora-dpo-probe-20260624

## User Request

Use all currently available generated_v5 Stage1-ready data for V2V-5 prefix-aware warmup, run 2 epochs with bf16, using the previously discussed LoRA location, then regenerate 500 loser pairs with the new model and supervise the generated videos.

## Data

- Unique Stage1-ready clips found: 3299
- Train rows: 3299
- Val/test rows: 100 mirrored from train for monitoring only
- Dataset: `local_assets/stageA_v2v5_all_available_c_r4_2epoch/dataset`
- Split report: `reports/stageA_v2v5_warmup_all_available/all_available_split_summary.md`

## LoRA Scope

Using the C loser-source scope from the small-LoRA sweep:

- `camera_conditioning`
- `self_attention`
- last 4 blocks: block_start=36, block_end=39
- rank=4, alpha=4, dropout=0.05

This matches the PPT conclusion that C is the medium-hard loser source, while B is the stable generator/baseline.

## Training Plan

- Model: LingBot-Fast V2V-5 wrapper
- Prefix frames: 0-4
- Prediction/loss frames: 5-80
- Precision: bf16 mixed-safe
- GPUs: physical H20 GPU4-7 only
- num_epochs: 2
- gradient_accumulation_steps: 4
- Expected optimizer steps: 414
- Save/eval every: 103 optimizer steps

## Runtime Safeguards

- `PYTHONNOUSERSITE=1` is required to avoid the user-site Python initialization hang introduced after metric/VBench work.
- Launcher blocks GPU0-3.
- Outputs remain under `local_assets/` and are not pushed.

## Cleanup Policy

No checkpoint, weight, raw HDF5, converted Stage1 data, or actively referenced artifact is deleted automatically. A cleanup candidate inventory will be built first; only clearly disposable temp/log/cache outputs are eligible for deletion.
