# E09 Training Summary

Decision before video: `TRAINING_SIGNAL_PASS_EARLY_STOPPED_FOR_VIDEO_EVAL`

E09 was stopped after the step50 checkpoint because it had a strong early scalar signal and GPU4 was needed for true V2V-5 video evaluation. The video gate then failed, so E09 is not a valid DPO recipe.

- Rows written: 52
- Final step: 51
- Final winner improvement post: 0.0012439489364624023
- Mean winner improvement post: 0.0005244211508677556
- Final winner contribution ratio: None
- Mean winner contribution ratio: None
- Final loser degradation post: -0.0012015700340270996
- Mean loser degradation post: -0.00048219699126023514
- Final decision after true-video audit: `VISUAL_GATE_FAIL_STEP050_WORSE`

See `checkpoint_eval/video_audit_summary.md`.
