# PPT Win/Lose Showcase Notes

这个视频展示 V2V-5 DPO preference-pair protocol 的可视化结果：prefix frames 0-4 是条件，WIN/LOSE 只比较 future frames 5-80。

- 输出 MP4: `reports/ppt_winlose_showcase_latest/winlose_showcase_for_ppt.mp4`
- 选中 pair 数: 5
- TypeA recommended: 4
- TypeB diagnostic blur failed: 1

## 本视频展示什么

主要展示 Protocol v3 当前真正可用的 TypeA controlled local corruption pairs：clean GT future 是 WIN，local corrupted future 是 LOSE。这适合讲 LocalDPO-style / controlled corruption 的数据构造逻辑。

## TypeB 当前结论

视频最后包含 1 个 TypeB diagnostic 段落，只作为反例：rollout loser 有 reward/energy margin，但 sharpness_ratio 低于 gate，属于 blur failed，不能作为训练用 rollout negative。

## PPT 主例子

- 主讲推荐: `protocol_v3_A_020_030_02222_collision_orbit_right_64_seed41222_wrong_camera_motion_local`
- failure: `wrong_camera_motion_local`
- reason: TypeA 可读、WIN/LOSE 清楚、reward margin 为正。

## LocalDPO / controlled corruption 推荐讲法

- LocalDPO 推荐: `protocol_v3_A_020_030_02222_collision_orbit_right_64_seed41222_wrong_camera_motion_local`
- 说明: prefix 不变，只在 future 的局部时间/空间区域构造可解释 LOSE，避免 rollout blur 成为偏好信号。

## 当前结论

- TypeA 可用于 protocol 展示和 LocalDPO-style engineering。
- TypeB rollout loser 仍需要更清晰的 candidate generator；当前不进训练。
- DPO 工程已跑通，但 objective signal 仍弱，不 scale。
