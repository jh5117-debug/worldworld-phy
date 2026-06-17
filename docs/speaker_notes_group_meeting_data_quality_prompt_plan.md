# Speaker Notes: TDW Data Quality and Prompt Plan

## Slide 1: 本周汇报主题
这一周我主要不是想证明模型已经训好了，而是想检查我们的 TDW 数据和 prompt 描述能不能支撑后面的训练。TDW 是 ThreeDWorld，一个可以生成物理场景视频的仿真环境。现在结论是，流程可以跑通，但视频质量还不够。所以下一步我想先把数据和 prompt 做扎实，而不是急着做偏好学习或者 DPO。

## Slide 2: 我们目前已经有的数据
这一页讲的是我们现在的数据基础。TDW v5 aggressive 2x 已经有 1000 条，train、val、test 是 800、100、100。这里的 target.mp4 probe passed 意思是视频文件能正常读取。use_action=false 表示我们现在不使用真实动作控制，只用第一帧、prompt 和相机轨迹作为条件。这里的问题主要不是 TDW GT 本身，而是模型看到 prompt 后生成的视频还不稳定。

## Slide 3: 现在最大的数据问题：prompt 太弱
prompt 就是模型看到的文字说明。如果这个文字太泛，模型只知道这是一个合成物理场景，但不知道具体有几个物体、谁在动、谁撞谁。所以后面它很容易乱猜，比如多生成几个物体，或者把前景物体变形。我们试过 template-aware 和 object-aware prompt，但如果没有负约束，object-aware 反而也可能让模型 hallucinate，也就是凭空想象出不存在的东西。

## Slide 4: 我们应该如何写一个完整的视频 prompt
这里我想把 prompt 当成一种标注规范。不是只写一句物理场景，而是要告诉模型：前景是什么，背景是什么，动作是什么，相机怎么动，以及什么事情不能发生。前景要写颜色、形状、数量、位置和初始状态。负约束也很重要，比如不能新增物体、不能删物体、不能把刚体融化成一团。

## Slide 5: 标准 prompt 模板
这几个模板不是最终答案，但可以作为下周整理数据和训练 prompt 的出发点。Drop、collision、roll、containment 每类物理事件都要写清楚动作和约束。比如 collision 里要明确谁撞谁、从哪个方向撞、撞完以后应该保持刚体运动。这样模型至少不会只靠模糊的场景描述去猜。

## Slide 6: 当前 StageA rollout 可视化结果
这页是最关键的失败分析。四列分别是 GT、Base、StageA step200 和 StageA final。StageA 是 warmup 的一个阶段，warmup 指正式训练前先让模型适应我们的 TDW camera-moving 数据。现在可以看到，虽然训练链路能跑，但生成视频里的前景物体还是不稳定：物体会变形、消失，或者多出 GT 没有的东西。所以现在不能说模型已经学好了。

## Slide 7: 当前定量结果
这里有些指标是 proxy，也就是简化版本，不是完整标准实现，所以我主要把它当成趋势参考。PMF 越高越好，FVD 越低越好，PSNR/SSIM 越高越好，LPIPS 越低越好。表里 StageA final 有一点点提升，但 Base 在 FVD proxy 上还是最好。这个结果说明 StageA 没有明显崩，但也没有形成很强的提升。

## Slide 8: 下一步：先把数据和 prompt 做好
下周我想先把数据问题解决，而不是直接做后面的偏好优化。第一步是用完整 prompt 规范重新整理训练入口。第二步是继续修 TDW multi-display，之后分阶段扩数据，先加 1000，不直接冲 5000。后面如果要选负样本，也不能选特别烂的视频，而是选质量还可以、但物理或者相机稍微差一点的 hard negative，也就是困难负样本。
