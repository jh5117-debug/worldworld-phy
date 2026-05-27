#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.data.convert_to_lingbot_cam_inputs \
  --manifest "${MANIFEST:-manifests/physion_cam_physgeo_smoke.jsonl}" \
  --out "${OUT:-data/physion_cam_lingbot_inputs_smoke}" \
  --source physion_movingcam \
  --num_frames "${NUM_FRAMES:-81}" \
  --fps "${FPS:-16}" \
  --size "${SIZE:-480x832}" \
  --use_action false \
  --make_dummy_action true \
  --limit "${LIMIT:-3}"
