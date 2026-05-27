# Physion Data Preview Report

Contact sheets were generated with:

```bash
python -m cam_physgeo.eval.make_contact_sheet \
  --manifest local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --source physion_movingcam \
  --out_dir local_assets/reports/contact_sheets/physion_data_preview \
  --limit 10 \
  --frames 0 10 20 30 40 50 60 70 80
```

Outputs:

- Gallery HTML: `local_assets/reports/contact_sheets/physion_data_preview/index.html`.
- Markdown gallery: `local_assets/reports/contact_sheets/physion_data_preview/gallery.md`.
- Per-sample JPG contact sheets in the same directory.

The preview covers the first 10 smoke-manifest samples and is suitable for checking camera motion, foreground object visibility, and reobserve-style trajectories. Drop/reobserve samples are the best immediate PPT examples because they show both object dynamics and camera-conditioned re-entry behavior.

