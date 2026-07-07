# v14 Objective Search Summary

- `E02_smoke10`: objective=`calibrated_winner_detached_log`, steps=`10`, training=`TRAINING_SIGNAL_FAIL_WINNER`, video=`NOT_RUN`, final_winner=`-4.172325134277344e-05`
- `E03_smoke10`: objective=``, steps=`2`, training=`TRAINING_SIGNAL_FAIL_WINNER`, video=`NOT_RUN`, final_winner=`-8.20159912109375e-05`
- `E02_best7`: objective=`calibrated_winner_detached_log`, steps=`7`, training=`TRAINING_SIGNAL_PASS`, video=`VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`, final_winner=`0.00033855438232421875`
- `E04_screen5`: objective=`no_lose_gap_normalized_win_only`, steps=`5`, training=`TRAINING_SIGNAL_PASS`, video=`VISUAL_GATE_FAIL_FINAL_CHECKPOINT_WORSE`, final_winner=`0.00013786554336547852`
- `E05_screen5`: objective=`normalized_clipped_loser`, steps=`5`, training=`TRAINING_SIGNAL_PASS`, video=`NOT_RUN`, final_winner=`0.00012230873107910156`

Current decision: `DPO_RECIPE_NOT_FOUND_V14`. E02_best7 and E04_screen5 have training signal but fail visual gate; E05_screen5 has training signal and still requires checkpoint video audit before it can be considered. Train400/S32/S64 remain blocked.
