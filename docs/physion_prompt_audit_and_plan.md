# Physion Prompt Audit And Plan

Physion does not provide LingBot-style natural language prompts as the primary condition. The pipeline generates prompts from template, scenario metadata, object metadata when safe, and camera motion.

Prompt levels:

- P0: `A synthetic physical scene.`
- P1: structured generic physical scene prompt with camera trajectory.
- P2: template-aware prompt for drop, collision, containment, roll, support, dominoes, drape, or link.

P2 avoids leaking labels:

- no `trial_complete`;
- no exact contact/no-contact answer;
- no frame number for reappearance;
- no evaluation label;
- no action/WASD wording.

P2 may say that the camera follows the provided trajectory and that persistent scene identity matters for lookaway/offscreen/reobserve motions.
