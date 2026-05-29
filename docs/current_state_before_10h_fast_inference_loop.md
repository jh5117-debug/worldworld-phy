# Current State Before 10h Fast Inference Loop

Date: 2026-05-29

## Worktree

- Remote execution worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`
- Remote branch during execution: `physion-lingbotfast-t5-debug`
- Project-local `local_assets` in the auxiliary worktree points to the same project assets as the main project tree.
- No data, weights, checkpoints, HDF5, MP4, NPY, or safetensors were moved or deleted.
- Local code branch prepared for push: `physion-lingbotfast-actual-inference-autoloop`

## Gate State

- T5 tokenizer: passed.
- T5 checkpoint stat/read/torch.load/load_state_dict: passed in the previous probe.
- T5 GPU bf16 full encode: passed, embedding shape `[[6, 4096]]`.
- Official LingBot-Fast actual demo: not previously run.
- cam_physgeo actual inference: not previously run successfully before this loop.
- Fast rollout batch, reward-on-rollout, VideoGPA encode, DPO, Stage1, and training: not allowed in this round.

## Assets

- LingBot-Fast active root: `local_assets/weights/lingbot_fast`
- LingBot-Base companion T5/VAE root: `local_assets/weights/lingbot_base`
- LingBot runtime code root: `local_assets/third_party/lingbot_world`
- Sample root: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`
- Sample used by the loop: `physion_movingcam_07abddf5748b`

## Known Pre-Loop Risk

The T5 blocker was resolved by increasing timeout and using GPU bf16. The remaining unknown was whether LingBot-Fast could consume the Physion camera condition format during actual generation.
