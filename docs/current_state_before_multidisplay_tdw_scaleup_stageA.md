# Current State Before Multidisplay TDW Scaleup + Stage A

## Dataset

- `tdw_v5_1000_lingbot_manifest.jsonl` exists: yes.
- Manifest count: 1000.
- Valid samples: 1000.
- target.mp4 probe pass: 1000 / 1000.
- Template distribution: `{'drop': 300, 'collision': 300, 'roll': 200, 'containment': 200}`.
- Camera distribution: `{'orbit_left_72': 300, 'orbit_right_64': 150, 'strafe_left_180': 150, 'orbit_right_60': 200, 'orbit_left_44': 200}`.
- use_action=false is preserved in the manifest and conversion path.
- Split exists: train 800 / val 100 / test 100.

## Scene / Prompt Audit

- Scene hash unique count: 1000 / 1000.
- Duplicate scene hash count: 0.
- First-frame phash unique count: 969 / 1000.
- First-frame phash duplicate count: 31.
- Unique prompt count: 1.
- Generic prompt ratio: 1.000.

The data is structurally valid and scene-diverse enough for warmup, but the prompt side is blocked: all 1000 samples still use one generic prompt.

## Rollout / Reward / Pair State

Prompt-aware rollout showed template-aware prompts are safer than the previous object-aware prompts. The object-aware prompt often caused foreground object hallucination. Quality-bounded hard negative mining produced smoke candidates, but reward confidence stayed below the DPO-ready gate. DPO training was not run and should not run from the current pair smoke.

## TDW Display State

- `DISPLAY=:8` works and reports NVIDIA OpenGL.
- `DISPLAY=:9` to `:13` respond to `xdpyinfo`, but report Mesa llvmpipe, not NVIDIA. They are not valid TDW GPU displays.
- `DISPLAY=:14` and `:15` fail.
- Root batch-mode access was unavailable from the ubuntu session, so automatic Xorg setup was not performed.

## Minimal Executable Path

1. Use the current 1000 data for Stage A only after prompt-v2 manifest is selected.
2. Configure real NVIDIA Xorg displays for `:9` to `:15` before TDW multi-display smoke.
3. Do not run 8-display smoke or scale-up until every display reports NVIDIA OpenGL renderer.
4. Do not run DPO; next DPO-related work remains quality-bounded pair diagnostics only.
