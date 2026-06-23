# 2026-06-23 Teacher Update CN

## 30 秒口头稿

这周我把 TDW camera-moving 数据到 LingBot-Fast StageA 的训练链路继续往前推了。现在优化本身是能工作的：formal StageA high-only 的 fixed-val loss 从 step100 到 step800 下降了大约 35%。但是生成视频质量还没有真正解决，前景物体仍然会消失、复制、变形，物理事件也不稳定，所以现在还不能进入 DPO。

## 2 分钟口头稿

这周的重点不是直接做 DPO，而是确认 StageA warmup 到底有没有带来可用的视频质量提升。我们做了 Original Fast、StageA step800 和 StageA final883 的同条件对比，每个样本保持同一个首帧、prompt、poses、intrinsics 和 seed。结果是训练指标看起来是正向的，fixed-val loss 有明显下降，说明优化链路没有坏；但可视化里 StageA 并没有稳定超过 base，很多样本出现了额外物体、前景碎片、物体消失和事件不保真。

我还补了两个几何一致性诊断：Epipolar Geometry 和 Camera-Conditioned SGC。Epipolar 主要看静态背景在输入相机位姿下是否符合极线几何；C-SGC 是我们当前的 camera-conditioned 版本，检查背景不同区域估计出来的相机运动是否一致，以及是否和输入 camera pose 一致。现在这两个指标能跑通，但 reward calibration 还没达标，所以只能作为诊断，不能直接作为 DPO reward。

下一步我建议先不要做偏好训练。更合理的是继续补全 generated_v5 数据转换和完整 detailed prompt，同时扩大训练数据覆盖，再做 full-data high-only StageA。等生成质量达到基本可用，再做 quality-bounded hard negative mining。

## 当前结论

- StageA optimization: PASS
- StageA generation quality: FAILED_OR_MIXED
- Physical consistency: PRELIMINARY
- BF16: FORMAL_READY，单卡/2卡/7卡 20-step preflight 均通过
- Full-data StageA: READY_TO_PLAN，但不应在本轮直接启动长训练
