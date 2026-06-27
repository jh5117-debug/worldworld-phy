# EXP Prefix-Aware Anchored DPO Probe

Updated: 2026-06-27T17:40:45

Status: **FAILED_FOR_SCALEUP**.

## Question

Can a tiny prefix-aware anchored DPO probe improve future-segment V2V-5 generation without degrading foreground identity, quality, or camera adherence?

## Input

- Pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Pair count available: 50
- Probe count: 5 pairs
- Prefix: frames 0-4
- Winner/loser future: frames 5-80
- Loss/reward: future-only

## Backend

- Real LingBot-Fast flow-matching energy backend.
- Policy/reference winner-loser energies are real model calls, not fake MSE proxies.
- Reference is frozen.
- Winner/loser use same timestep and same noise.
- Camera-conditioning LoRA rank 4, 160 modules, 6,553,600 trainable parameters.

## Runtime Result

- Single-GPU tiny probe ran 20 optimizer steps.
- no SIGFPE / no OOM / no NaN or Inf.
- Adapter save/load worked.

## Learning Result

| Metric | Value |
|---|---:|
| mean DPO loss | 0.693144497 |
| final DPO loss | 0.693165958 |
| mean implicit accuracy | 0.600 |
| final implicit accuracy | 0.000 |
| mean winner improvement | 0.000084573 |
| final winner improvement | -0.000231806 |

The preference signal is weak/inconclusive and does not justify scale-up.

## Video Result

DPO step20 underperforms the StageA final checkpoint on future-only PSNR/SSIM and visually shows extra object fragments. Decision: `DPO_PROBE_FAILED`.

## Next Step

Do not scale DPO. Rebuild quality-bounded pair selection with stronger rewards and harder-but-not-collapsed negatives. Keep clean GT winners for diagnostics; do not use current StageA/DPO rollouts as winners.
