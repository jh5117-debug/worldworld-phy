Current Status: PASS

# FVD Backend Audit

A local real video-FVD path is available after auditing an older I3D backend:

- Script found: `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/eval_fid_fvd.py`
- I3D TorchScript weights found: `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/i3d_torchscript.pt`
- Original external script had a tensor-layout bug for this environment (`[B,T,H,W,C]` sent to a model expecting `[B,3,T,H,W]`).
- A repaired smoke path was run with correct `[B,3,T,H,W]` layout.
- Tiny smoke status: PASS
- Tiny smoke FVD score: 0.6614066493904447

Caveats:

- This validates backend availability only.
- The 4-clip score is not a publication/stable FVD benchmark.
- Full FVD should use a larger, fixed evaluation set and the corrected layout.
- Image FID was not used as FVD.
