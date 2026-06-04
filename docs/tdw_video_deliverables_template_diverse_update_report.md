# TDW Video Deliverables Template-Diverse Update Report

Date: 2026-06-04

## Status

No new template-diverse videos were added to the deliverables gallery.

## Reason

The template-diverse 10-sample actual run failed the generation/validation gate:

- planned templates: `drop:3`, `collision:3`, `roll:2`, `containment:2`;
- non-drop templates failed at upstream argument parsing;
- validation accepted count: `0`;
- suitable_for_warmup count: `0`.

## Existing Deliverables

The existing video deliverables under:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

were not modified with failed template-diverse samples.

## Next Update

After a fixed template-diverse actual run passes validation and conversion, add a new section:

`TDW v2 template-diverse warmup_mild smoke`

with one row per accepted sample.

