# Broad-LoRA vs Camera-Only LoRA Diagnosis

Updated: 2026-06-24 CST  
Branch: `research/quant-small-lora-dpo-probe-20260624`

## Short Conclusion

The large quality gap between last week's camera-only tiny LoRA and this week's broad-LoRA is most likely caused by the trainable scope, not by prompt quality.

Last week's adapter was a constrained camera-conditioning adapter: about 4 LoRA tensors and about 40,960 trainable parameters. It could nudge the camera-control pathway without substantially rewriting LingBot-Fast's original visual generation prior. That made it visually safer.

This week's broad-LoRA touched camera conditioning, self-attention, cross-attention, and FFN across 560 Linear layers, with about 102.9M trainable parameters. On a small/partial StageA dataset, that is enough capacity to overfit the forward-loss objective and damage foreground identity, object shape, and physical event priors. The fixed-val loss can improve while generation quality gets worse.

## What Changed Between the Two Runs

| Item | Last week camera-only tiny LoRA | This week broad-LoRA |
| --- | --- | --- |
| Main purpose | Gentle camera adapter | Broad StageA optimization |
| Trainable scope | Camera conditioning only | Camera + self-attn + cross-attn + FFN |
| Matched modules | Very small, around 4 LoRA tensors | 560 Linear layers |
| Trainable params | About 40,960 | About 102,891,520 |
| Dataset scale | Small warmup gate | Partial generated_v5/balanced StageA |
| Visual outcome | More stable, though not final | `FAILED_OR_MIXED`; foreground and physics degraded |
| Risk profile | Low: hard to rewrite visual prior | High: can rewrite main DiT denoising behavior |

## Why Better Prompts Did Not Fix This

The prompt did improve: it became more structured and more informative. But prompt quality is only one control input. If the adapter update damages the model's internal visual prior, a better prompt cannot fully recover object persistence, rigid shape, or event dynamics.

In this run the failure mode is consistent with over-broad adaptation:

- Foreground object identity became unstable.
- Objects could deform, disappear, duplicate, or change color.
- Physical events were not preserved reliably.
- Camera/background behavior did not improve enough to compensate.
- The loss curve looked better than the generated videos.

That means the StageA loss was not a sufficient proxy for DPO candidate quality.

## Most Likely Root Cause

The main error was treating broad-LoRA fixed-val loss improvement as evidence that the adapter was a better generator.

The better interpretation is:

1. Broad-LoRA had too many trainable parameters for the available data.
2. It optimized the high-noise forward objective, but that objective did not protect foreground identity or physical event quality.
3. Updating attention and FFN paths gave the adapter enough freedom to disturb LingBot-Fast's original generation prior.
4. The dataset was still too small and too narrow to support 102M trainable parameters.
5. The reward/benchmark was not yet strong enough to stop a visually bad adapter early.

## Current Correction

Broad-LoRA is no longer the main route for candidate generation.

The active correction is a small-LoRA sweep:

- A: camera-only rank 4.
- B: camera-only rank 8.
- C: camera conditioning + limited self/temporal attention, selected blocks only.
- D: camera conditioning + limited cross-attention, selected blocks only.

The goal is to keep the adapter small enough to preserve LingBot-Fast's visual prior while still testing whether limited attention LoRA helps camera/background consistency.

## DPO Data Collection Implication

The project goal is DPO preference-data collection, not making broad-LoRA look good.

The safest DPO route is anchored preference data:

- Winner can be clean GT.
- Loser can be controlled corrupted GT.
- Loser can also be a model rollout only if it passes a quality floor.

Do not use completely collapsed videos as DPO losers. If the loser is too bad, DPO may learn trivial artifacts instead of the intended physical or camera preference.

Quality-bounded loser requirements:

- Not black or corrupt.
- Not globally frozen.
- Main foreground object still exists.
- No total scene replacement.
- Visual quality above a minimum floor.
- Failure should be specific: wrong camera, background drift, object deformation, event failure, or reobserve mismatch.

If generated rollouts remain too poor, then the first DPO probe should use GT winners versus controlled corrupted GT losers, not bad rollout versus worse rollout.

## Practical Decision

For the next candidate generator:

1. Prefer Original LingBot-Fast or last week's camera-only tiny LoRA as baselines.
2. Compare against small-LoRA sweep candidates using the fixed Quant Benchmark v1.
3. Use broad-LoRA only as a diagnostic or negative candidate, and only if the video passes the minimum quality floor.
4. Do not select DPO pairs solely by low reward score; select hard negatives that are still visually valid.
