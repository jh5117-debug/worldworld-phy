# DPO Literature Integration

Updated: 2026-06-28T00:20:04

This note records the actual sources read for this protocol pass and maps them to the current Cam-PhysGeo V2V-5 setting.

## Sources Read

1. LocalDPO / *Mind the Generative Details: Direct Localized Detail Preference Optimization for Video Diffusion Models*
   Source: arXiv `https://arxiv.org/abs/2601.04068` (`2601.04068v4`, updated 2026-05-20).
   Key source facts: it treats high-quality real videos as positives, creates negatives by local spatio-temporal corruption/restoration, and uses region-aware DPO restricted to affected areas.

2. Diffusion-SDPO / *Safeguarded Direct Preference Optimization for Diffusion Models*
   Source: arXiv `https://arxiv.org/abs/2511.03317` (`2511.03317v2`, updated 2025-12-02).
   Key source facts: standard diffusion DPO can enlarge the margin while degrading both winner and loser; SDPO scales loser gradients to preserve winner quality.

3. Linear-DPO / *Linear Direct Preference Optimization for Diffusion and Flow-Matching Generative Models*
   Source: arXiv `https://arxiv.org/abs/2605.21123` (`2605.21123v1`, published 2026-05-20).
   Key source facts: it derives a diffusion/flow-matching DPO objective, argues sigmoid DPO can be mismatched for regression-style generation, and proposes sustained linear utility plus EMA reference.

## LocalDPO Mapping To This Project

What transfers directly:

- Use clean TDW/Physion GT future as the positive winner.
- Build controlled local corruptions rather than relying only on ranking multiple bad rollouts.
- Record affected region, affected time span, and affected mask for each negative.
- Prefer local, explainable failure dimensions: background drift, wrong camera, object deformation, identity shift, reobserve mismatch, partial freeze, and local physics failure.

What cannot be copied directly:

- LocalDPO is text-to-video and region-aware DPO; our current LingBot-Fast DPO energy path is prefix-conditioned V2V-5 and flow-matching based.
- We do not yet have a region-masked DPO energy loss. Protocol v1 stores affected masks so the next trainer can restrict loss/reward to affected regions.

Current implementation:

- Type A pairs in `manifests/dpo_preference_protocol_v1_pairs.jsonl` use clean GT future versus future-only local corruptions.
- Prefix frames 0-4 remain unchanged and are never corrupted.

## Diffusion-SDPO Mapping To This Project

What transfers directly:

- The previous tiny DPO failure looked loser/winner-unstable: loss stayed near 0.693 and videos got worse.
- Future DPO logs must separately track `winner_improvement`, `loser_degradation`, and reference-relative margin.
- A DPO run should fail if the margin comes mainly from making loser worse while winner does not improve.

What cannot be copied directly:

- The SDPO derivation is diffusion-image centric; LingBot-Fast is video and flow-matching with camera conditions.
- We need an equivalent safe-lambda on the flow-matching energy gradient, not just an image diffusion loss.

Protocol consequence:

- Pair generation now rejects collapsed losers and chooses medium-hard negatives.
- Reports explicitly keep winner quality and loser collapse fields.

## Linear-DPO Mapping To This Project

What transfers directly:

- LingBot-Fast uses flow-matching-like energy, so the Linear-DPO framing is closer than classic NLP sigmoid DPO.
- The near-constant DPO loss around 0.693 suggests sigmoid DPO can under-signal in this setting.
- Continuous reward margins should be retained in the pair manifest rather than only binary winner/loser labels.

What cannot be copied directly:

- We have not implemented Linear-DPO or EMA reference in the trainer yet.
- Current protocol only prepares pair data; no DPO objective change is trained in this round.

Protocol consequence:

- Each protocol v1 pair stores `reward_margin`, reward vectors, quality metadata, and pair type.
- The next trainer can choose sigmoid DPO, SDPO, or Linear-DPO using the same manifest.

## Our Innovation Space

- Prefix-aware V2V-5: clean frames 0-4 condition future frames 5-80.
- Known camera pose/intrinsics are part of the condition and future-only scoring.
- Medium-hard loser protocol avoids both trivial collapsed losers and ambiguous near-ties.
- Local affected-region corruption allows future region-aware DPO.
- Reobserve-specific local corruption is world-model-specific and not just generic aesthetic alignment.
- Staged data plan: Type A controlled local corruption first, then Type B GT-vs-rollout, and only later Type C rollout-vs-rollout if winner absolute quality passes.
