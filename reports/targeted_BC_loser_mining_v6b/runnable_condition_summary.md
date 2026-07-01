# Runnable Condition Summary v6b

Current Status: PASS

- Source: `manifests/quant_benchmark_v1_core.jsonl`
- Selected: 32 conditions, balanced 8 per template where available.
- Runnable: 32 / 32
- Template distribution: {'drop': 8, 'collision': 8, 'roll': 8, 'containment': 8}
- Prefix/future recovery method: cut frames 0-4 into prefix mp4 and frames 5-80 into GT future mp4 from existing target full video.
- This explains v6: it only used already materialized DPO prefix5 assets (5 condition dirs), while quant benchmark full videos needed prefix/future materialization.
