#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.data.convert_to_lingbot_cam_inputs --manifest "${MANIFEST:-manifests/cam_physgeo_train.jsonl}" --out "${OUT:-data/cam_physgeo_lingbot_inputs/train}" --num_frames 81 --fps 16 --size 480x832 --use_action false --make_dummy_action true "${@}"
