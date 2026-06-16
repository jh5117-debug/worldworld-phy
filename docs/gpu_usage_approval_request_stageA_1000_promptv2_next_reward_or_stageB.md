# GPU Usage Approval Request: StageA 1000 PromptV2 Next Reward Or StageB

Current rollout visual eval completed: GT/Base/StageA step200/StageA final for 12 conditions.

## Option A: Reward v5 scoring on this rollout
Use the existing 12-condition comparison and run reward v5 scoring only. No DPO. This is recommended if human review shows StageA final is not visually worse than Base.

## Option B: Prefer step200 if human review likes it
Step200 had best validation loss during training, but proxy metrics do not clearly beat final. Use step200 only if visual review prefers it.

## Option C: Prefer final if human review agrees
Final is slightly better on PMF_proxy, PSNR, SSIM, and LPIPS_proxy. If human review agrees, use final for reward scoring.

## Option D: Stage B / larger LoRA scope
If both adapters remain too close to Base or object physics is poor, request a Stage B mixed/low-noise pilot or a broader LoRA target. No DPO yet.

## Safety
No reward scoring, no pair construction, and no DPO were run in this task. User approval is required before any next GPU job.
