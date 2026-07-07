# E06_screen20 Checkpoint Eval Blocker

- Decision: `CHECKPOINT_EVAL_BLOCKED_WANI2VFAST_INIT`
- Training signal: `PASS` for 20 steps, but final recipe gate requires real checkpoint videos.
- Parallel eval attempt: step000 and step020 both stalled at `instantiate WanI2VFast`, with no real GPU allocation and `0` MP4s.
- Single retry: step020 on physical GPU5 also stalled at `instantiate WanI2VFast` for more than 6 minutes, with GPU5 around 4 MiB and `0` MP4s.
- Result: E06 remains `TRAINING_SIGNAL_ONLY`; it is not a valid DPO recipe.
