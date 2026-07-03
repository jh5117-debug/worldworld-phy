Current Status:
PPT_SHOWCASE_READY_H264

# DPO Pair Factory v10 PPT Notes

这个视频展示 5 个 v10 preference pair：1 个真实 rollout-derived GT>C，4 个 controlled synthetic visible TypeM-v10。所有 pair 都共享 prefix/prompt/poses/intrinsics，WIN 是 clean GT future 或高质量 winner，LOSE 是 medium-hard negative。

当前 v10 ready pool: 81 pairs = 18 existing strict + 63 synthetic visible. Synthetic negatives 必须与真实 rollout TypeB 分开标注。

MP4: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_ready_showcase.mp4`
Selected CSV: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_selected_pairs.csv`
