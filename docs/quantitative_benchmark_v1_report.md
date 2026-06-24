# Quantitative Benchmark v1 Report

Status: MANIFEST_READY; rollout and metric execution pending small-LoRA sweep checkpoints.

## Dataset

- All conditions: 80
- Core: 64
- Stress: 16
- Train sample overlap: 0
- Train scene overlap: 0

## Core Selection

Core benchmark uses val/test-holdout rows only and excludes train sample_id and scene_group_id. It contains 16 conditions per template: drop, collision, roll, containment.

## Stress Selection

Stress benchmark uses remaining non-train camera-heavy/OOD-style rows. Current generated_v5 reobserve manifest is empty, so stress is marked diagnostic and does not claim true reobserve coverage.

## Template Distribution

```json
{
  "drop": 16,
  "collision": 22,
  "roll": 22,
  "containment": 20
}
```

## Camera Distribution

```json
{
  "orbit_left_72": 16,
  "orbit_right_64": 16,
  "orbit_right_60": 22,
  "orbit_left_44": 20,
  "strafe_left_180": 6
}
```

## Manifests

- `manifests/quant_benchmark_v1_all.jsonl`
- `manifests/quant_benchmark_v1_core.jsonl`
- `manifests/quant_benchmark_v1_stress.jsonl`
- `manifests/quant_benchmark_v1_summary.json`

## SHA256

```json
{
  "all": "e7ba0f973073989930be897478ff426dcbea2e3eb5c741850947c3ceef66d691",
  "core": "4cc498fc42be83679e17af4e1806bba2e27b57e601054d5370c10a3391e1a868",
  "stress": "ecbffab044d9d7761110a3bd140e8b281f54e8afee4979c3cc8cf189c1c33b33"
}
```

## Next

After small-LoRA sweep checkpoints are available, run fixed-seed rollout for Original Fast, prior tiny camera-only LoRA, broad-LoRA step800/final883, and the four small-LoRA candidates. Then compute the quantitative metric table and perform full video audit.
