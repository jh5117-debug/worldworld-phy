# v14 Objective Search Summary

- `E02_smoke10`: objective=`calibrated_winner_detached_log`, steps=`10`, training=`TRAINING_SIGNAL_FAIL_WINNER`, video=`NOT_RUN`, final_winner=`-4.172325134277344e-05`
- `E03_smoke10`: objective=`lower_lr_calibrated_winner_detached_log`, steps=`2`, training=`TRAINING_SIGNAL_FAIL_WINNER`, video=`NOT_RUN`, final_winner=`-8.20159912109375e-05`
- `E02_best7`: objective=`calibrated_winner_detached_log`, steps=`7`, training=`TRAINING_SIGNAL_PASS`, video=`VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`, final_winner=`0.00033855438232421875`
- `E04_screen5`: objective=`no_lose_gap_normalized_win_only`, steps=`5`, training=`TRAINING_SIGNAL_PASS`, video=`VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`, final_winner=`0.00013786554336547852`
- `E05_screen5`: objective=`normalized_clipped_loser_alpha002`, steps=`5`, training=`TRAINING_SIGNAL_PASS`, video=`VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`, final_winner=`0.00012230873107910156`
- `E01_screen20`: objective=`calibrated_winner_detached_raw`, steps=`20`, training=`TRAINING_SIGNAL_PASS`, video=`EVAL_NOT_ATTEMPTED_TRAINING_SIGNAL_ONLY`, final_winner=`0.0002976655960083008`
- `E06_screen20`: objective=`normalized_clipped_loser_alpha005`, steps=`20`, training=`TRAINING_SIGNAL_PASS`, video=`CHECKPOINT_EVAL_BLOCKED_WANI2VFAST_INIT`, final_winner=`0.00028055906295776367`

Current decision: `DPO_RECIPE_NOT_FOUND_V14`. E01 and E06 newly passed 20-step training signal, but E06 checkpoint video eval is blocked at WanI2VFast initialization and E01 has not passed the video/metric/Codex audit gate. Earlier E02_best7/E04/E05 also failed visual gates. Train400/S32/S64 remain blocked.
