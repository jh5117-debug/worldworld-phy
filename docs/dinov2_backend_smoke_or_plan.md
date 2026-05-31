# DINOv2 Backend Smoke Or Plan

## Result

- DINOv2 directory exists: `local_assets/weights/dinov2`
- Local DINOv2 checkpoint files: none found.
- Forward smoke: not possible.
- Current visual feature path: proxy only.

## Plan

Recommended small model:

- `dinov2_vits14`
- Target path: `local_assets/weights/dinov2`
- Estimated size: hundreds of MB depending on checkpoint format.
- HF token: unknown, depends on source.
- User approval: required before download.

## Reward Impact

Until DINOv2-small is present and wired:

- R_fg remains proxy/fallback.
- R_reobs remains proxy/fallback.
- Feature-backed rollout preference should not be used for DPO pair selection.
