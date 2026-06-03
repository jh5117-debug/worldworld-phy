# TDW Generation v2 LingBot Conversion Report

## Status

Partial.

The generated HDF5 was accepted and converted into LingBot cam-only camera
condition assets. The target MP4 writer/probe remained unstable in the remote
run, so this conversion is not yet a complete LingBot warmup sample.

## Converted Sample

| Item | Value |
|---|---|
| Sample id | `tdw_v2_00000_drop_orbit_left_12_seed10000_0000` |
| Output dir | `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00000_drop_orbit_left_12_seed10000_0000` |
| Source HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5` |
| `poses.npy` | present, `(81, 4, 4)` |
| `intrinsics.npy` | present, `(81, 4, 4)` projection matrices |
| runtime LingBot intrinsics | convertible to `(81, 4)` |
| `action.npy` | present, dummy zeros, `(81, 4)` |
| action norm | 0.0 |
| `use_action` | false |
| `metadata.json` | present |
| `depth.npy` | present |
| `id_mask.npy` | present |
| `image.jpg` | present after direct first-frame fallback |
| `target.mp4` | file was emitted, but remote probe did not validate it |

## Code Updates

- `validate_generated_hdf5.py` now computes target visibility, max consecutive
  invisible frames, camera path length, and contact sheets.
- `convert_generated_to_lingbot.py` now reads validation JSON and converts only
  accepted samples.
- `physion_hdf5_reader.py` now handles optional inconsistent arrays without
  blocking camera conversion and adds PIL fallback for encoded image bytes.
- `utils/video.py` now has stricter MP4 writer fallbacks, but the remote sample
  still needs one final probe-confirmed rerun after SSH stabilizes.

## Gate Decision

Do not run 10-sample TDW smoke yet.

Reasons:

- The HDF5 generation and validation gate passed.
- The camera-condition conversion gate mostly passed.
- The target video file needs probe-confirmed MP4 output before this sample is
  treated as a complete LingBot cam-only warmup sample.
- Any 10-sample run on `DISPLAY=:8` would use GPU0 and needs separate approval.
