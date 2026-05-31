# Current State Before DINO Reward V5 Camera Stress

## Prior Round Summary

- 8-frame camera ablation succeeded.
- Previous sample `physion_movingcam_07abddf5748b`:
  - repeat A vs repeat B pixel L1: `0.0`
  - correct vs frozen pixel L1: `0.0`
  - correct vs exaggerated-yaw pixel L1: `0.02547`
- Camera video-level effect before this round: partial. Strong camera perturbation affected output, but correct/frozen remained identical in that sample.
- RAFT-small real flow: forward passed.
- Flow shape: `[1, 256, 448, 2]`
- Reward v4:
  - clean avg: `0.9996`
  - Fast avg: `0.7618`
  - clean > Fast: `3/3`
  - Fast bg/cam used real flow.
- DINOv2 before this round: checkpoint missing; no forward.

## Gates Before This Round

- Gate A: passed.
- Gate B: passed.
- Gate C: partial.
- Gate D: partial; DINO missing.
- Gate E: VideoGPA encode not allowed.
- Gate F: DPO not allowed.
