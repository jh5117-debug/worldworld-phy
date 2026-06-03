#!/usr/bin/env bash
set -euo pipefail
python3 -m cam_physgeo.data.tdw_generation_v2.convert_generated_to_lingbot "$@"
