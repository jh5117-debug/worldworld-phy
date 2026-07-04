Current Status: PASS_WITH_RUNTIME_CAVEAT

# v12 LoRA Scope Candidate Summary

## L0_camera_r4

- Description: camera conditioning only, rank 4
- Target groups: `['camera_conditioning']`
- Rank/alpha: 4 / 4
- Blocks: 0..None
- Estimated trainable params: `6553600`
- Memory risk: low

## L1_camera_r8

- Description: camera conditioning only, rank 8
- Target groups: `['camera_conditioning']`
- Rank/alpha: 8 / 8
- Blocks: 0..None
- Estimated trainable params: `13107200`
- Memory risk: low_medium

## L2_camera_temporal_r4

- Description: camera conditioning plus limited early self/temporal attention, rank 4, max 4 blocks
- Target groups: `['camera_conditioning', 'self_attention']`
- Rank/alpha: 4 / 4
- Blocks: 0..3
- Estimated trainable params: `RUNTIME_SCOPE_SANITY_REQUIRED`
- Memory risk: medium

## L3_camera_cross_r4

- Description: camera conditioning plus limited early cross attention, rank 4, max 4 blocks
- Target groups: `['camera_conditioning', 'cross_attention']`
- Rank/alpha: 4 / 4
- Blocks: 0..3
- Estimated trainable params: `RUNTIME_SCOPE_SANITY_REQUIRED`
- Memory risk: medium_high

## L4_adaln_camera_mod_r4

- Description: camera / pose-conditioned AdaLN or scale-shift modulation if modules exist
- Target groups: `['camera_conditioning']`
- Rank/alpha: 4 / 4
- Blocks: 0..None
- Estimated trainable params: `6553600`
- Memory risk: low_unknown

## Caveat

Camera-conditioning module count and params are from a historical runtime-verified preflight. Self/cross/AdaLN candidates still require winner-anchor runtime sanity before DPO. FFN/broad/all-block scopes remain forbidden.
