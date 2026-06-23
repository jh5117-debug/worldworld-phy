# 2026-06-23 Next Experiments CN

## 下一步优先级

1. 完成 generated_v5 raw -> conversion -> stage1-ready 的数据门，保证每条样本有 target/video、poses、intrinsics、prompt 和 metadata。
2. 继续完善 detailed prompt，避免 generic prompt 让模型乱猜物体和事件。
3. 用当前 partial full snapshot 做 preflight，不启动长训练；等 converted 数据分布更完整后再跑 full-data high-only StageA。
4. 做 LoRA scope 对比：camera-only、camera+self-attn、camera+cross-attn、camera+temporal/FFN。
5. 继续验证 BF16：单卡、2 卡、7 卡都通过后，才允许把 BF16 写成 formal ready。
6. 生成质量基本可用之后，再做 reward calibration 和 quality-bounded hard negatives。

## 暂时不做

- 不做 StageB。
- 不做 DPO。
- 不做 GRPO。
- 不做 pair mining。
- 不做大规模 rollout。

## 老师可能追问

Q: 为什么 loss 降了但视频还是差？
A: loss 说明模型在训练分布上能优化 denoising/flow 目标，但生成视频还要求前景身份、物理事件和长时序一致性。现在 LoRA 和数据/prompt 还不足以稳定这些因素。

Q: 现在能不能 DPO？
A: 不建议。负样本太差会让 DPO 学到低质量偏好边界，应该先提高候选质量并建立 quality floor。

Q: Epipolar / C-SGC 是 reward 吗？
A: 现在先是诊断指标。clean/corrupt calibration 还没达标，所以不能直接当 DPO reward。
