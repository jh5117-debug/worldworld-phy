# Final Report: TDW v5 Aggressive 2x 1k Generation On GPU0

Date: 2026-06-14

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` for TDW / Unity generation. The approved scope was adding 800 TDW v5 aggressive 2x samples to the existing human-approved 200, for a total dataset size of 1000.

No training, DPO, VideoGPA 03_train, Stage1, rollout, reward scoring, checkpoint, LoRA, or optimizer state was run.

## Generation

- Planned new samples: 800
- Generated HDF5: 800/800
- Failed generation count: 0 observed
- GPU/display: GPU0 / `DISPLAY=:8`
- Raw HDF5 root: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_1k_scaleup_800samples/`

New 800 distribution:

- drop: 240
- collision: 240
- roll: 160
- containment: 160

## Validation

- HDF5 validation OK: 800/800
- Suitable for warmup: 800/800
- Strict suitable_for_visible_motion: 212/800
- Delayed camera motion: 0/800
- Unique scene hash: 800/800
- Duplicate scene hash: 0

The strict visible-motion count is conservative for this aggressive v5 profile. The dataset is accepted here based on human approval plus HDF5 completeness, warmup suitability, start0 camera motion, visibility, and scene diversity.

## Conversion

- New 800 LingBot cam-only conversion: 800/800
- target.mp4 probe during conversion: passed
- use_action=false
- dummy action.npy generated
- Conversion root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_scaleup_800/`

## Combined 1000 Dataset

- Combined manifest rows: 1000
- Audit valid samples: 1000/1000
- target.mp4 video probe: 1000/1000
- Duplicate sample IDs: 0
- ready_for_dataloader: true

Combined template distribution:

- drop: 300
- collision: 300
- roll: 200
- containment: 200

Combined camera distribution:

- orbit_left_72: 300
- orbit_right_60: 200
- orbit_left_44: 200
- orbit_right_64: 150
- strafe_left_180: 150

## Split

- train: 800
- val: 100
- test: 100

The split is balanced by template and camera_variant.

## Review Pack

- Review pack: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_1000/`
- Gallery: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_1000/video_gallery.html`
- Review subset videos: 100
- Per-template subset: 25 each for drop, collision, roll, containment
- Full video list: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_1000/full_video_list.txt`

## Safety

- No training.
- No DPO.
- No VideoGPA 03_train.
- No Stage1.
- No rollout.
- No reward scoring.
- No local_assets committed.

## Next Action

Use the TDW v5 aggressive 2x 1000 dataset for LingBot-Fast camera-conditioned warmup on GPU4-7. After warmup, run controlled rollout/reward/pair gates. DPO remains later and requires separate approval.

