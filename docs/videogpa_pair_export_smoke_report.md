# VideoGPA Pair Export Smoke Report

Pair builder command:

```bash
python -m cam_physgeo.dpo.pair_builder \
  --manifest local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --source physion_movingcam \
  --pair_types gt_vs_corrupt \
  --out local_assets/data/physion/processed/dpo_pairs/smoke/dpo_pairs_physion_gt_vs_corrupt.jsonl \
  --corruptions background_drift object_deformation object_color_identity_change reobserve_mismatch freeze_foreground global_freeze \
  --limit 10 \
  --min_margin 0.15 \
  --save_videos local_assets/data/physion/processed/dpo_pairs/smoke/videos \
  --save_report local_assets/reports/dpo_pair_builder/smoke_report.md
```

Result:

- Kept pairs: 51.
- Rejected pairs: 9.
- Mean margin: 0.2956.
- Pair type: `gt_vs_corrupt`.
- Internal JSONL: `local_assets/data/physion/processed/dpo_pairs/smoke/dpo_pairs_physion_gt_vs_corrupt.jsonl`.

Per-corruption kept pairs:

- background_drift: 2.
- freeze_foreground: 10.
- global_freeze: 10.
- object_color_identity_change: 9.
- object_deformation: 10.
- reobserve_mismatch: 10.

VideoGPA export:

- Output JSON: `local_assets/data/physion/processed/dpo_pairs/smoke/videogpa_pairs.json`.
- Groups exported: 51.
- Missing required fields: 0.

The export keeps prompt, winner/loser videos, and camera condition paths in `extra_condition`. No VideoGPA training was run.

