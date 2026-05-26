#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.data.validate_manifest --manifest "${MANIFEST:-manifests/cam_physgeo_all.jsonl}" "${@}"
