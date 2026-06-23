# 2026-06-23 Results Summary CN

## 已完成

- 生成了 8 条 test_holdout 条件的会前对比：Original Fast / StageA step800 / StageA final883。
- 每条都使用相同 initial image、prompt、poses、intrinsics、seed、scheduler 和 81 帧 480x832 设置。
- contact sheets 已生成：`local_assets/meeting_eval_20260624_011137/contact_sheets/`
- 定性评分 CSV：`reports/meeting_eval_20260624_011137/qualitative_scores.csv`
- 定量训练曲线：`reports/meeting_eval_20260624_011137/metrics/`
- Epipolar 和 C-SGC clean/corrupt calibration 已完成。
- M0/M1/M2 生成视频几何指标已完成。

## 训练指标

- formal StageA high-only 完成 883 step。
- fixed-val 从 step100 到 step800 下降约 35.4%。
- 未发现非有限 loss。
- step 883 overshoot 的原因是旧 target gate 在 epoch 边界检查，commit 7631276 已修复为 epoch 内停止。

## 视觉结果

- Base 和 StageA 都能生成视频。
- StageA 没有稳定优于 Base。
- 主要失败：前景物体不稳定、物体复制/消失/变形、物理事件不保真、局部彩色碎片。

## 指标结论

- Epipolar/C-SGC 可以作为 camera/background 诊断。
- clean/corrupt reward calibration overall clean>worse 只有约 0.50，没有达到 0.85。
- 不能把当前 reward 标记为 DPO-ready。
