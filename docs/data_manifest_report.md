# Data Manifest Report

- total samples: 2827
- PhyInOne samples: 2472
- movingcam_synthetic samples: 355
- has pose: 2827
- has intrinsics: 2827
- has depth: 355
- has id mask: 355
- usable for Stage1: 2497
- usable for reward calibration: 2827
- reobserve split candidates: 348

## Templates

- drop: 751
- collision: 731
- unknown: 666
- roll: 352
- containment: 231
- support: 96

## Camera Motions

- unknown: 2155
- static: 324
- relative_yaw_180_reobserve: 173
- lookaway_up_reobserve: 69
- offscreen_z_reobserve: 59
- occluder_lookaway_reobserve: 34
- offscreen_x_reobserve: 12
- reobserve: 1

## Notes

- Full manifest uses fast path scanning by default; per-video fps/size/frame probing can be enabled with `CAM_PHYSGEO_PROBE_VIDEO=1`.
- HDF5 key deep audit can be enabled with `CAM_PHYSGEO_SCAN_HDF5_KEYS=1`; current moving-camera rows include hdf5 URI candidates and fast-scan quality flags.
