# Framework Completeness Audit

A. data manifest: 8/10. Full JSONL manifest builds and validates on 2827 real samples; video probing is optional for speed.
B. PhyInOne scanner: 8/10. Reads real `video.mp4`, `poses.npy`, `intrinsics.npy`, prompt/depth/id sidecars when present.
C. moving-camera synthetic scanner: 8/10. Reads outputs plus HDF5/MP4 candidates, pose/intrinsics/depth/id HDF5 URI candidates; deep HDF5 key scan is optional.
D. LingBot cam-only input conversion: 8/10. Generates image/target/prompt/metadata and extracts HDF5 camera arrays when h5py is present; prefix video is supported.
E. action.npy fallback: 10/10. `use_action=false`; dummy zero action only for LingBot compatibility.
F. reward framework: 7/10. Runs end-to-end with deterministic CV/video proxies and backend TODOs for RAFT/depth/DINO.
G. corrupted negatives: 7/10. Planning records plus actual video corruptions for freeze/shuffle/drift; object-mask corruptions guarded by quality flags.
H. DPO pair builder: 8/10. Anchored GT>corrupt pairs with reward margins, schema and filtering.
I. Stage1 warm-up: 7/10. Delegates to legacy `physical_consistency.stages.stage1_physinone_cam.runner` with `control_type=cam`; long run guarded.
J. Stage2 anchored DPO: 6/10. Pair dataset and DPO loss ready; real LingBot logprob adapter remains TODO before long training.
K. Stage3 self-rollout DPO: 6/10. Gated dry-run entry and pass@K policy present; no ungated self-rollout.
L. eval/camera audit: 7/10. Manifest audit and LingBot path checks run; long inference launch remains explicit through legacy eval_batch/runtime.
M. GitHub cleanliness: 8/10. `.gitignore` blocks data/weights/checkpoints/videos/npy; staging must use explicit safe file list.
