#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.dpo.pair_builder --manifest "${MANIFEST:-manifests/cam_physgeo_train.jsonl}" --out "${OUT:-manifests/cam_physgeo_dpo_pairs.jsonl}" "${@}"
