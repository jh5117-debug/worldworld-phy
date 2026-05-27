# Framework Completeness Audit

A. Physion manifest: implemented and smoke-tested.

B. Official Physion scanner: implemented; returns warnings if standalone official data is missing.

C. Physion moving-camera scanner: implemented; reads real HDF5 layout, camera pose/position/aim, projection, depth, ID, object state, and templates from paths/metadata.

D. LingBot cam-only converter: implemented; writes image, target, poses, intrinsics/projection, prompt, metadata, optional depth/ID, and dummy zero action only.

E. Action conditioning: disabled. `action.npy` is compatibility fallback only.

F. Reward framework: runnable with Physion metadata hooks and CV fallbacks.

G. Corrupted negatives: implemented for video/HDF5-exported samples.

H. Anchored DPO pair builder: generates real corruptions, scores clean/corrupt, and filters by margin.

I. Stage1 warm-up: dry-run integrates with legacy LingBot/TRD path, real training guarded.

J. Stage2 DPO: pair dataset and energy DPO helper are ready; real LingBot logprob/energy adapter remains TODO.

K. Stage3 self-rollout: gated dry-run entry exists.

L. Eval/camera audit: smoke-tested.

M. GitHub hygiene: data, weights, checkpoints, HDF5, MP4, NPY/NPZ, manifests, and reports are gitignored.
