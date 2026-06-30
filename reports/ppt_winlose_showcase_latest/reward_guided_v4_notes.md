# Reward-Guided v4 PPT Notes

Current Status: PASS_SHOWCASE_GENERATED

- Showcase MP4: `reports/ppt_winlose_showcase_latest/winlose_showcase_reward_guided_v4_for_ppt.mp4`
- Selected pairs: 5
- Showcase codec used by PyAV: libx264
- The video emphasizes TypeA+ and TypeM medium-hard negatives.
- TypeB rollout losers remain blocked by blur/quality and are not used as training-ready pairs.
- Best main example: first selected TypeM if present, otherwise first TypeA+.
- LocalDPO / controlled corruption example: first selected TypeA+.
