# Stage2 VideoGPA DPO Plan

Do not train yet. This project remains Physion-only, Fast-first, camera-conditioned, and no-action except for dummy compatibility files.

## Current Gate State

- Gate A: LingBot-Fast 1-sample actual inference passed.
- Gate B: 3-10 Fast rollout smoke is being validated by the rollout/reward autoloop.
- Gate C: camera condition ablation is being validated with correct/frozen/reversed poses.
- Gate D: reward-on-real-Fast-rollout is being validated after the small rollout set exists.
- Gate E: VideoGPA encode smoke is not allowed in the current phase.
- Gate F: LingBotFastVideoGPAAdapter winner/loser batch shape dry-run is not allowed in the current phase.
- Gate G: real DPO energy/logprob adapter is not wired and remains blocked.

## Why DPO Training Is Still Blocked

1. Small Fast rollout quality and failure modes must be inspected before pair generation grows.
2. Camera ablation must show whether poses/intrinsics materially affect generation. If correct/frozen/reversed look the same, the camera adapter must be fixed first.
3. Reward must separate clean GT from real Fast rollout failures, not only artificial corrupted negatives.
4. Feature backends must be reported honestly: DINO/V-JEPA/VideoMAE/flow may still be proxy or fallback in parts of the current reward path.
5. VideoGPA encode has not been run in this phase and should wait until Gates B-D are understood.
6. `LingBotFastVideoGPAAdapter.compute_dpo_energy_or_logprob` must not be faked.

Only after Gates B, C, and D are reasonably passed should a future round attempt VideoGPA encode smoke. DPO training remains disallowed until all gates A-G pass.

## Camera / Reward Debug Update

- Gate A: passed.
- Gate B: passed at small-smoke level with 3 Fast rollouts.
- Gate C: not proven. Camera tensors reach `WanI2VFast.generate` through `action_path`, and LingBot-Fast source builds `c2ws_plucker_emb`, but strong ablation did not produce enough successful variants to show output differences above stochastic baseline.
- Gate D: failed / not reliable. Raw reward still ranks Fast above clean GT. Confidence-aware aggregation lowers absolute scores and marks rows provisional, but it still wins only 1/3 pairs.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next gate is not VideoGPA. The next minimal work is camera embedding instrumentation plus reward backend repair.

## Plucker / Reward Backend Debug Update

- Gate A: passed.
- Gate B: passed at 3-rollout smoke level.
- Gate C: partial. Direct probe of LingBot's actual `get_plucker_embeddings` path shows correct/frozen/reversed/exaggerated camera variants produce different `c2ws_plucker_emb` control tensors. This proves camera condition reaches the model-side embedding. Video-level effect is still not proven because the same-seed ablation set did not complete.
- Gate D: failed / not reliable. V2 reward aggregation now marks all proxy/missing components as low confidence and adds real-backend-only totals, but no real backend is active for clean or Fast in the rollout scorer. Raw and proxy totals still rank Fast above clean.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work before VideoGPA is either: finish a small video-level camera ablation after GPU 6/7 are free, or wire real reward backends for clean GT depth/ID/camera/object-state and generated rollout feature/flow.

## Camera Effect / Reward Real Backend Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial. Camera/control tensors differ across camera variants and source-level DiT camera scale/shift injection is present. Runtime full-DiT scale/shift tensors were not captured, and video-level effect is still not proven because the 4-frame ablation is invalid for the current LingBot-Fast temporal latent path.
- Gate D: partial. Clean GT real metadata backend is active for depth, ID mask, camera, intrinsics, and object-state metadata. Reward v3 ranks clean above Fast on 3/3 pairs, but Fast rollout scoring remains fallback/proxy because generated-video DINO/flow/depth are not real yet.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: LingBotFastVideoGPAAdapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work remains outside VideoGPA: run a valid 8-frame video-level camera ablation, wire real optical-flow forward from local RAFT assets, and add DINOv2-small only after user approval.

## Video Camera / Flow / DINO Smoke Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial/pass. Embedding-level and DiT camera path remain confirmed. The valid 8-frame ablation completed at 256x448: same-seed repeat difference was `0.0`, frozen matched correct, and exaggerated-yaw produced nonzero output difference (`pixel_l1=0.02547`). This proves a strong camera perturbation can affect video output, but ordinary camera sensitivity still needs stronger/longer validation.
- Gate D: partial. Clean GT real backend remains active. RAFT-small real optical-flow forward now works and contributes to Fast rollout `bg`/`cam` real components. DINOv2-small is still missing, so `fg`/`reobs` feature terms remain proxy/fallback and reward is not DPO-ready.
- Gate E: VideoGPA encode remains not allowed until camera video effect and reward backends are both reliable.
- Gate F: LingBotFastVideoGPAAdapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work is still not VideoGPA: add DINOv2-small after approval and re-run reward-on-rollout with both real flow and real feature backends.

## DINO Reward V5 / Camera Stress Update

- Gate A: passed.
- Gate B: passed.
- Gate C: pass/partial. A high-yaw stress sample was selected (`physion_movingcam_13db379640ce`). The 8-frame 480x832 stress ablation generated all six variants. Same-seed repeat stayed `0.0`; reversed, exaggerated-yaw, and exaggerated-translation diverged from repeat baseline. Frozen still matched correct.
- Gate D: partial/pass for smoke. DINOv2-small was downloaded to `local_assets/weights/dinov2/dinov2_vits14/` and forwards successfully. Reward v5 uses clean GT metadata, RAFT real flow, and DINO real features; clean > Fast remains `3/3`.
- Gate E: VideoGPA encode smoke may be considered next, but only encode smoke. Do not train.
- Gate F: DPO remains not allowed.
- Gate G: real DPO energy/logprob remains unimplemented.

Next permitted step is VideoGPA encode smoke only. DPO training is still blocked.

## VideoGPA Encode Smoke Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Stress camera perturbations have video-level effect, but ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 provides a usable smoke-level clean > Fast signal with RAFT and DINO active, but generated depth/mask/physics are still not complete.
- Gate E: partial. VideoGPA pair export and encode-readiness smoke passed for `gt_vs_fast` metadata/video readability, and camera sidecars were preserved. Native latent encode did not run because LingBot-Fast VAE/condition encoding is not wired into VideoGPA.
- Gate F: still no. DPO remains blocked.
- Gate G: still no. `compute_dpo_energy_or_logprob` is intentionally `NotImplementedError`.

Next minimal step is not training. It is a LingBot-Fast VideoGPA adapter dry-run that implements real LingBot VAE latent encode, same-noise/same-timestep batch collation, and a non-fake energy/logprob path.

## LingBot VAE / Energy Dry-Run Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Camera stress perturbations have video-level effect, but ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 has clean > Fast on the 3-sample smoke with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: partial/pass for latent/condition/batch plumbing. LingBot `Wan2_1_VAE` loads, winner/loser videos encode to LingBot-compatible latents, camera condition packs into a nonzero Plucker/control tensor, and a same-noise/same-timestep 1-pair batch shape dry-run passes.
- Gate F: still no. Energy/logprob remains `NotImplementedError`; no DPO loss, backward, optimizer, LoRA save, or model update was run.
- Gate G: still no. Real DPO training remains blocked.

Next minimal step is to wire the real LingBot-Fast denoising/velocity forward target for `compute_dpo_energy_or_logprob`. Only after that may a future round consider a 1-pair DPO scalar-loss dry-run, still without real training unless explicitly approved.

## LingBot Energy Forward Debug Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Camera stress perturbations have video-level effect, while ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 has clean > Fast on the 3-sample smoke with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: passed for 1-pair plumbing smoke. VideoGPA pair/metadata, LingBot latent encode, condition encode, same-noise/same-timestep batch, real LingBot model forward, and policy energy dry-run all pass.
- Gate F: no. DPO training remains disallowed.
- Gate G: partial. Real policy energy is wired with a code-backed flow target (`noise - x0`), but frozen reference energy and scalar DPO loss have not been run.

Energy dry-run details:

- Policy model: `WanModelFast` through `WanI2VFast`.
- Target: flow velocity `noise - x0`.
- Winner energy: `0.8652140498161316`.
- Loser energy: `0.8322668075561523`.
- Reference: deferred, not faked.
- Backward / optimizer / LoRA / checkpoint save: none.

Next permitted step is only a user-confirmed 1-pair scalar DPO loss dry-run
with a real frozen reference, no optimizer, and preferably no backward. Real
DPO training remains blocked.

## Reference Energy / Scalar Loss Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair no-backward DPO plumbing. VideoGPA pair/metadata,
  LingBot latent encode, condition encode, batch shape, policy energy,
  reference energy, and scalar DPO loss dry-run all pass.
- Gate F: no. DPO training remains disallowed.

Reference/scalar details:

- Reference model: same frozen LingBot-Fast checkpoint as policy base.
- Reference load: passed sequentially under `torch.no_grad()`.
- Reference energy: `E_ref_winner=0.8652140498161316`,
  `E_ref_loser=0.8322668075561523`.
- Policy energy: `E_policy_winner=0.8652140498161316`,
  `E_policy_loser=0.8322668075561523`.
- Beta: `0.1`.
- Scalar loss: `L_DPO=0.6931471824645996`.
- Backward / optimizer / LoRA / checkpoint save: none.

Because policy and reference are identical frozen weights in this smoke,
`Delta_policy == Delta_ref` and the scalar loss is `log(2)`. This validates the
formula and tensor plumbing, not preference learning. The next permitted step is
only a user-confirmed 1-pair backward-only dry-run with no optimizer and no
saved weights. Real DPO training remains blocked.

## DPO Backward-Only Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair backward-only plumbing with fallback
  `tiny_subset`.
- Gate F: no. Real DPO training remains disallowed.

Backward-only details:

- Reference energy: passed with frozen same LingBot-Fast checkpoint.
- Scalar DPO loss: passed.
- Primary `camera_adapter` gradient scope: failed with CUDA OOM at the current
  8-frame 480x832 latent size.
- Fallback `tiny_subset`: passed.
- Trainable fallback params: `head.head.bias`, `head.head.weight`.
- Trainable param count: `327,744`.
- Params with grad: `2`.
- Reference params with grad: `0`.
- Optimizer / optimizer step / checkpoint / LoRA save: none.

Next permitted step is not real training. If the user confirms, the next round
may do only a 1-pair optimizer-step dry-run, preferably after adding a smaller
LoRA/camera-adapter trainable scope. Large/multi-pair DPO training remains no.

## DPO Trainable Scope Sweep Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: partial/pass. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  and backward-only have all passed for plumbing scopes. A camera-aware scope
  sweep has now been attempted.
- Gate F: no. Real DPO training remains disallowed.

Scope sweep details:

- `tiny_subset`: passed, `327,744` trainable params.
- `head_only`: passed, `337,984` trainable params.
- `plucker_projection_only`: OOM, peak about `100.44 GB`.
- `action_scale_shift_tiny`: OOM, peak about `100.48 GB`.
- `camera_lora_tiny`: skipped because no existing LoRA params were injected.

Conclusion: the only passing scopes are still output-head plumbing scopes.
Existing camera bias scopes are semantically better but still retain too much
autograd graph at the current 8-frame 480x832 latent size. The next permitted
step is only to implement a tiny real LoRA/camera adapter injection path and
rerun backward-only. Do not run optimizer step yet. Real DPO training remains
blocked.

## Tiny LoRA Camera-Control Backward Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  and backward-only all pass. A meaningful runtime camera-control LoRA scope now
  also passes backward-only.
- Gate F: no. Real DPO training remains disallowed.

LoRA backward-only details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Trainable params: `40,960`.
- Loss: `0.6931474208831787`.
- LoRA params with grad: `4`.
- Base params with grad: `0`.
- Reference params with grad: `0`.
- NaN/Inf gradients: no.
- Optimizer / optimizer step / LoRA save / checkpoint save: none.

Next permitted step is only a user-confirmed 1-pair optimizer-step dry-run on
this LoRA scope, with no save and explicit before/after parameter checks. Real
DPO training and multi-pair training remain blocked.

## LoRA Optimizer-Step Dry-Run Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, and tiny camera-control LoRA backward-only all pass. A 1-pair
  / 1-step optimizer-step dry-run on the same LoRA scope also passed.
- Gate F: no. Real DPO training remains disallowed.

Optimizer-step dry-run details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, one param group, LoRA params only.
- Trainable params: `40,960`.
- Step count: `1`.
- `L_DPO_before`: `0.6931473016738892`.
- LoRA params changed: yes, max abs diff `9.981580660678446e-06`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- NaN/Inf gradients: no.
- LoRA save / checkpoint save: none.
- `restore_after_step`: passed; runtime LoRA params were restored in memory.

Next permitted step is not real training. If the user explicitly confirms, the
next round may do only a 1-pair overfit mini-loop such as 5 optimizer steps on
the same pair, no checkpoint, no LoRA save, and no multi-pair training.

## DPO 1-Pair Overfit Mini-Loop Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, tiny camera-control LoRA backward-only, and 1-pair
  optimizer-step dry-run all pass. A bounded 1-pair / 5-step runtime LoRA
  mini-loop also passed.
- Gate F: no. Real DPO training remains disallowed.

Mini-loop details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, LoRA params only.
- Steps: `5` on the same pair.
- Noise/timestep: resampled each step, but shared between winner and loser
  within each step.
- Loss values: `[0.6931473016738892, 0.6931471228599548,
  0.6931470632553101, 0.6931471228599548, 0.6931472420692444]`.
- LoRA params changed: yes, max abs diff `4.924208769807592e-05`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- LoRA params with grad: `4` each step.
- Base params with grad: `0` each step.
- NaN/Inf gradients: no.
- OOM: no.
- LoRA save / checkpoint save: none.
- `restore_after_loop`: passed; runtime LoRA params were restored in memory.

Because noise and timestep were resampled each step and the policy starts from
the same checkpoint as the reference, monotonic loss decrease is not expected in
this smoke. The run confirms finite repeated steps, stable gradients, LoRA-only
updates, and base/reference immutability.

Next permitted step is not real training. If the user explicitly confirms, a
future round may do only a tiny 5-pair or 10-pair overfit smoke, or a fixed
noise/timestep 1-pair diagnostic. Saved LoRA remains disabled by default, and
multi-pair real DPO training remains blocked.

## Fixed-Noise DPO Diagnostic Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, tiny camera-control LoRA backward-only, 1-pair optimizer-step,
  1-pair 5-step resampled mini-loop, and a fixed-noise/fixed-timestep
  diagnostic all pass at the plumbing/safety level.
- Gate F: no. Real DPO training remains disallowed.

Fixed diagnostic details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, LoRA params only.
- Steps: `10` on the same pair.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- Loss values: `[0.6931471228599548, 0.6931471824645996,
  0.6931471824645996, 0.6931471824645996, 0.6931472420692444,
  0.6931471824645996, 0.6931472420692444, 0.6931472420692444,
  0.6931471824645996, 0.6931471824645996]`.
- Loss monotonic: no.
- Loss delta: `+5.960464477539063e-08`.
- Preference logits stayed near zero, around `1e-7`.
- LoRA params changed: yes, max abs diff `0.0001006147067528218`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- NaN/Inf gradients: no.
- OOM: no.
- LoRA save / checkpoint save: none.
- `restore_after_loop`: passed.

Interpretation: fixed-noise plumbing and safety passed, but the overfit signal
is weak and not monotonic at rank 2 / lr `1e-5`. The sign convention is still
consistent: larger positive preference logit lowers DPO loss, but the observed
logits are extremely small. This is not a reason to launch real training.

Next permitted step is not real training. If the user explicitly confirms, the
next round may do either a stronger fixed-noise sensitivity diagnostic, or a
very small 5-pair/10-pair overfit smoke with saved LoRA disabled. Full DPO
training remains blocked.

## GitHub Remote Integrity Gate

Future push steps must target the user-visible repository:

- Correct repo: `jh5117-debug/worldworld-phy`
- Fixed remote:
  `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote: `world_model_phys.git`

Before pushing any branch, run:

```bash
git remote -v
git ls-remote --heads origin
```

The push is allowed only if `origin` fetch and push URLs both match the fixed
remote above. Do not push code, docs, or reports to a remote containing
`world_model_phys.git`. The helper script
`scripts/check_github_remote_integrity.sh` performs this check and should be
used before future push operations.


## Current DPO Status Before TDW Generation v2

DPO engineering gates are mostly passed for smoke: VideoGPA pair/metadata dry-run, LingBot latent encode, condition encode, same-noise/same-timestep batch, policy energy, reference energy, scalar DPO loss, LoRA backward, optimizer-step dry-run, and 1-pair mini-loop have all been validated. However, signal sensitivity remains weak, the 5-pair tiny overfit was skipped, and real DPO training is still not allowed.

Before any real training, we need stronger signal through a fixed-noise LR/scope sweep and a better data pool. TDW / Physion-style moving-camera v2 generation is therefore needed for camera-conditioned warmup and later reward-selected top/bottom winner-loser pairs. No VideoGPA 03_train, no Stage1, and no real DPO training should run at this stage.

## TDW Generation v2 Mild-Smoke Gate

The TDW / Physion-style generation v2 wrapper now has an explicit
`warmup_mild` camera set. The plan-level blocker that allowed possible
stress/reobserve leakage is fixed:

- allowed mild variants: `orbit_left_12`, `orbit_right_12`,
  `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`;
- banned warmup terms: lookaway, offscreen, reobserve, relative-yaw-180,
  occluder, extreme;
- 10-trial dry-run plan check: `bad_count=0`.

Actual TDW generation is still gated by display/GPU routing. The observed TDW
display `:8` appears to be configured on GPU0, while the current task only
allows GPU6/7. Therefore 1-sample actual TDW generation must wait for either a
GPU6/7 TDW display or explicit user approval. This does not change DPO gates:
real DPO training remains `no`.
