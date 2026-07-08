#!/usr/bin/env bash
set -euo pipefail

NAS_ROOT="${NAS_ROOT:-/mnt/workspace/hj/nas_hj}"
OUTPUT_JSON="${OUTPUT_JSON:-reports/migration/pai_restore_packet.json}"
SUMMARY="${SUMMARY:-reports/migration/pai_restore_packet.md}"

python3 -m cam_physgeo.orchestration.physeditworld_pai_restore_packet \
  --nas_root "$NAS_ROOT" \
  --output_json "$OUTPUT_JSON" \
  --summary "$SUMMARY"

printf 'PhysEditWorld PAI restore packet written: %s %s\n' "$OUTPUT_JSON" "$SUMMARY"
