# 简洁 PPT Notes：DPO Pair Showcase

## 1. 当前 DPO pair 可视化结论
这次整理的是 V2V-5 prefix-aware preference pair：prefix frames 0-4 作为条件，winner/loser 只比较未来 frames 5-80。最终展示用 pair 以 Type B 为主，也就是 clean GT future 赢过 medium-hard rollout future；这最接近后续真正 DPO 数据。

## 2. 为什么之前 loser 看起来糊
主要不是 contact sheet 后处理导致。contact sheet 会缩小画面，让视频看起来更软，但源 MP4 本身就是 StageA/Fast rollout，细节和前景稳定性不足。当前 quality floor 没有显式 sharpness threshold，所以一些不崩但偏软的 rollout 会通过。

## 3. 新选择的 pair
- Pair 1: background drift + hallucinated fragments；winner R=1.000000，loser R=0.663222，margin=0.336778，status=diagnostic_blur_failed。
- Pair 2: extra object / identity instability；winner R=1.000000，loser R=0.694814，margin=0.305186，status=diagnostic_blur_failed。
- Pair 3: wrong camera following + weak event；winner R=1.000000，loser R=0.663222，margin=0.336778，status=diagnostic_blur_failed。
- Pair 4: partial freeze / weak physical event；winner R=1.000000，loser R=0.694814，margin=0.305186，status=diagnostic_blur_failed。
- Pair 5: controlled local wrong-camera motion；winner R=1.000000，loser R=0.740000，margin=0.260000，status=recommended。

## 4. 主例子
如果要讲 pair protocol 的问题，建议主讲 Pair 1：`protocol_v1_B_008_prefix5_anchored_95981b8f74bed0_background_drift_stageA_final`，它能说明 Type B rollout loser 虽有 reward/energy margin，但 blur gate 不够严。若要讲可用的 clean preference pair，建议主讲最后一个 Type A controlled corruption。

## 5. StageA warmup LoRA 结论
StageA V2V-5 warmup 只挂 camera-conditioning LoRA，rank=4，alpha=4，dropout=0.05，只跑了 100 high-noise steps；没有 self-attention/cross-attention/FFN LoRA，没有 low-noise detail branch。它更像是在调相机条件使用，不足以修 texture sharpness、foreground identity 和 object deformation。模糊不太像 overfitting，更像 LoRA scope 太窄 + high-noise-only objective mismatch + rollout 本身质量不足。

## 6. 下一步 quality floor
加入 loser_sharpness_ratio >= 0.55、visual_quality >= 1、R_quality >= candidate p40、禁止 severe blur/低码率重编码 artifact。如果 loser 的失败类型不是 blur，就不要选明显糊的视频做 PPT case。
