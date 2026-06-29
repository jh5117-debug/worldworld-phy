# Loser Blur Audit

Audited medium-hard rollout losers: 16 Type B rows.
Rollout R_quality p40 threshold: 0.794.
Sharpness ratio range for Type B: min=0.049, median=0.049, max=0.192.
Rows marked drop-for-blur: 16.

## Answer

The selected loser videos are generated rollout futures, not a contact-sheet-only artifact. The contact sheets do downsample panels and make them look softer, but the source MP4s keep the expected 832x480-ish future-video resolution and are readable. The main blur/softness comes from the rollout model quality and low-detail generation, not from this PPT post-processing step.

Current quality floor is usable but too loose for presentation: it checks visual quality and collapse/freeze, but it does not explicitly reject low Laplacian sharpness or loser/winner sharpness ratio. Next version should require loser_sharpness_ratio >= 0.55, visual_quality >= 1, R_quality >= candidate p40, and severe-blur rejection unless blur itself is the intended failure.
