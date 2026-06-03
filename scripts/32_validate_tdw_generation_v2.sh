#!/usr/bin/env bash
set -euo pipefail
python3 -m cam_physgeo.data.tdw_generation_v2.validate_generated_hdf5 "$@"
