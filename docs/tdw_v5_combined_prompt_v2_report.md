# TDW v5 Combined Prompt v2 Report

## Why

Prompt-aware rollout showed the old template-aware prompt was safer than the old object-aware prompt. The object-aware prompt often hallucinated extra foreground objects, likely because it used generic category words and broad negative wording. Therefore v2 uses concise event text plus object-consistency constraints.

## Output

- Prompt-v2 manifest: `local_assets/experiments/exp_multidisplay_tdw_scaleup_promptv2_stageA/prompt_v2/manifest_combined_prompt_v2.jsonl`
- Prompt root: `local_assets/experiments/exp_multidisplay_tdw_scaleup_promptv2_stageA/prompt_v2/prompts`
- Count: 1000.
- Prompt variant: `combined_v2`.
- Inventory source: `first_frame_visible_objects_fallback` for all samples because metadata does not expose reliable readable object names/colors.

## Template Examples

### drop

A rigid object falls under gravity in a synthetic TDW physical scene. Follow the provided camera trajectory from the first frame. The scene contains only the foreground objects visible in the first frame. Do not create any additional objects. Preserve the initially visible foreground objects, object count, colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion.

### collision

A moving rigid object collides with another rigid object in a synthetic TDW physical scene. Follow the provided camera trajectory from the first frame. The scene contains only the foreground objects visible in the first frame. Do not create any additional objects. Preserve the initially visible foreground objects, object count, colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion.

### roll

A rigid object rolls across the surface in a synthetic TDW physical scene. Follow the provided camera trajectory from the first frame. The scene contains only the foreground objects visible in the first frame. Do not create any additional objects. Preserve the initially visible foreground objects, object count, colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion.

### containment

Rigid objects interact with a container in a synthetic TDW physical scene. Follow the provided camera trajectory from the first frame. The scene contains only the foreground objects visible in the first frame. Do not create any additional objects. Preserve the initially visible foreground objects, object count, colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion.

## Risk Mitigation

This avoids listing generic object categories such as balls/cubes/cones unless the metadata actually provides that exact inventory. It should reduce prompt-induced extra-object hallucination compared with the old object-aware prompt.
