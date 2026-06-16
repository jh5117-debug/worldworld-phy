# TDW v5 1000 Combined Prompt v2 Manifest Split Report

## Manifest

- Main prompt-v2 manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Exists: True
- Count: 1000
- Template distribution: `Counter({'drop': 300, 'collision': 300, 'roll': 200, 'containment': 200})`
- Prompt variant distribution: `Counter({'combined_v2': 1000})`
- Generic prompt count: 0 in the prompt-v2 manifest by construction.

## Split

- Train: 800
- Val: 100
- Test: 100
- Scene overlap: 0 according to split tool output.

## Prompt examples

### Example 1

A rigid object falls under gravity in a synthetic TDW physical scene. Follow the provided camera trajectory from the first frame. The scene contains only the foreground objects visible in the first frame. Do not create any additional objects. Preserve the initially visible foreground objects, object count, colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion.

## Ready for Stage A

Yes, as a data entrypoint. Training still requires explicit approval and GPU scheduling.
