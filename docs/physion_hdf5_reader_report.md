# Physion HDF5 Reader Report

Implemented:

- `cam_physgeo.data.physion_hdf5_audit`
- `cam_physgeo.data.physion_hdf5_reader`

Reader API:

`read_physion_sample(path) -> dict`

Returned fields:

- `rgb`
- `depth`
- `id_mask`
- `flow`
- `normals`
- `camera_pose`
- `camera_position`
- `camera_aim`
- `intrinsics`
- `object_states`
- `metadata`

The reader supports the TDW layout where per-frame data is under `frames/0000/...`, with RGB/depth/ID encoded in `_img`, `_depth`, and `_id`. It maps `camera_pose`, `camera_position`, `camera_aim`, `camera_matrix`, and `projection_matrix`. If camera pose is unavailable but position+aim exists, it computes a camera pose. If K-style intrinsics are unavailable but projection exists, it exports the projection-derived calibration matrix.
