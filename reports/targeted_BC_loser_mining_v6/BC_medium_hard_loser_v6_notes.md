# BC medium-hard loser v6 PPT notes

Current Status: PARTIAL / NOT_READY_FOR_DPO_SMOKE

- 展示内容：B/C targeted rollout 后，选出 4 条 GT > C rollout 的可见 medium-hard examples。
- B camera-only rank8：稳定、清楚，更适合作 candidate generator / control baseline。
- C camera+self/temporal rank4：在 collision 条件中更容易产生可解释的 foreground / physical-event / hallucinated-fragment failure。
- 当前 DPO-ready pair 数量只有 4，低于 >=10 的 tiny DPO smoke gate。
- 当前树里只有 5 条可运行 prefix5 conditions，无法执行真正 8-condition / 32-condition 扩展。
- 编码说明：远端无 ffmpeg/libx264 可执行文件，本 MP4 使用 OpenCV mp4v fallback。
- 结论：可以用于 PPT 展示 targeted mining 思路，但不要启动 DPO smoke。
