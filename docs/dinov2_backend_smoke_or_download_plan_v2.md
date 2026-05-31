# DINOv2 Backend Smoke Or Download Plan V2

## Local Check

- Weights root: `local_assets/weights`
- DINOv2 directory: `local_assets/weights/dinov2`
- Local checkpoint present: no
- Forward success: no
- Feature shape: null
- Output summary: `local_assets/reports/smoke/dinov2_backend_smoke_v2/summary.json`

The smoke did not download anything. It only checked the local asset tree.

## Recommended Minimal Backend

- Recommended model: `dinov2_vits14`
- Target path: `local_assets/weights/dinov2/dinov2_vits14`
- Expected size: hundreds of MB depending on checkpoint format.
- Token requirement: unknown; depends on download source.
- User approval needed: yes.

Draft command after approval:

```bash
mkdir -p local_assets/weights/dinov2/dinov2_vits14
# download dinov2_vits14 checkpoint here after approval
```

## Reward Impact

Without DINOv2-small forward:

- R_fg foreground identity remains proxy/fallback.
- R_reobs object/background similarity remains proxy/fallback.
- GeoFlow-style DINO feature consistency is not real.
- Reward-on-rollout should not be treated as DPO-ready even if clean > Fast ordering is correct.
