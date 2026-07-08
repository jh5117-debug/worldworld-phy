# PhysEditWorld 50h LingBot Conversion Report

Updated: 2026-07-08T18:29:06 CST

Decision: `CONVERSION_TOOL_READY_DATA_BLOCKED`

## Implemented

- `cam_physgeo.data.prompt_gravity`
- `cam_physgeo.data.lingbot_condition_schema`
- `cam_physgeo.data.physeditworld_to_lingbot`

## Gravity Conditioning

The v0 conversion uses prompt-only gravity:

```text
A first-person interactive world rollout.
The character follows the given action sequence and camera trajectory.
The scene is rendered under gravity: {gravity_value}g.
```

No gravity MLP or gravity embedding is introduced.

## Smoke Results

- Direct synthetic-row smoke: PASS.
- Empty real-manifest conversion: PASS, because the current strict PhysEditWorld train manifest has 0 rows.
- Output report: `reports/physeditworld_50h/conversion_smoke.csv`.
- Output summary: `reports/physeditworld_50h/conversion_smoke_summary.md`.
- Output LingBot train manifest: `manifests/physeditworld_50h_lingbot_train.jsonl` with 0 rows.

## Current Blocker

`PHYS_EDIT_WORLD_DATA_NOT_FOUND`: strict PhysEditWorld selected 50h data is not visible on H20. Conversion is ready but blocked on a valid manifest.
