# LoRA Scope Decision for DPO v12

Decision: `L0_camera_r4` is the only scope allowed for further tiny diagnostics.

Rationale:

- It was the only scope with 5/5 runtime pass, positive mean winner improvement, and positive final winner improvement.
- Camera-r8 had a larger update but ended with negative winner improvement.
- Camera+temporal and camera+cross were less stable and ended non-positive or negative.

This does not authorize large DPO. It only identifies the safest tiny diagnostic scope seen so far.
