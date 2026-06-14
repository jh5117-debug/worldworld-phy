# TDW v5 1k Scale-Up Generation Run Report

Date: 2026-06-14

## Execution

The new 800 TDW v5 aggressive 2x samples were generated on GPU0-bound `DISPLAY=:8`, as explicitly approved by the user for TDW / Unity generation.

Generation was split into eight 100-sample chunks:

- chunk_000: finished Sat Jun 13 12:16:16 CST 2026
- chunk_001: finished Sat Jun 13 15:47:15 CST 2026
- chunk_002: finished Sat Jun 13 19:22:50 CST 2026
- chunk_003: finished Sat Jun 13 22:57:50 CST 2026
- chunk_004: finished Sun Jun 14 02:35:11 CST 2026
- chunk_005: finished Sun Jun 14 06:02:52 CST 2026
- chunk_006: finished Sun Jun 14 09:50:42 CST 2026
- chunk_007: finished Sun Jun 14 13:40:34 CST 2026

## Result

- New HDF5 generated: 800/800
- Failed generation count: 0 observed in chunk logs
- Raw HDF5 root: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_1k_scaleup_800samples/`

## Safety

- Used GPU0 / `DISPLAY=:8` only for TDW / Unity generation.
- No training, DPO, VideoGPA, rollout, reward scoring, checkpoint, LoRA, or optimizer state was run or saved.

