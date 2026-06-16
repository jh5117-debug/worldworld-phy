# TDW Scaleup Prompt-Aware Rollout Plan

The old object-aware prompt should not be used directly because it often introduced extra foreground objects. The safer default is `combined_prompt_v2`:

- template event phrase;
- camera follows the provided trajectory from frame 0;
- foreground objects are exactly those visible in the first frame;
- short negative constraints against adding/removing/duplicating/morphing objects;
- stable background under camera motion.

Future rollout should compare Base / Stage A / Stage B with combined_prompt_v2 and 4-column videos. Hard-negative mining must apply the quality floor before DPO pair construction.
