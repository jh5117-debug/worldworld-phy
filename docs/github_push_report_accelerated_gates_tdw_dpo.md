# GitHub Push Report: Accelerated TDW and DPO Gates

## Result

Pushed successfully.

## Repository

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote:
  `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect repo avoided: `world_model_phys.git`

## Branch / Commit

- Branch: `physion-accelerated-gates-tdw-dpo`
- Final commit: branch HEAD for `physion-accelerated-gates-tdw-dpo`
  after the final amend/push.
- Commit message:
  `Accelerate remaining TDW and DPO gate smoke checks`

## Pushed Scope

Committed only code and docs:

- TDW validator/converter/video fallback updates;
- DPO `dpo_signal_sensitivity_fast` runner;
- PRD / gate / final reports.

## Excluded

Not committed or pushed:

- `local_assets/`;
- generated TDW HDF5 / MP4 / contact sheets;
- generated NPY / NPZ;
- model weights;
- LoRA weights;
- checkpoints;
- latents;
- large logs;
- third-party raw repositories.

## Verification

Before push, `git remote -v` showed the fixed `worldworld-phy` SSH remote. The
push command used GitHub SSH over port 443 and created the remote branch:

```bash
GIT_SSH_COMMAND='ssh -p 443' git push -u origin physion-accelerated-gates-tdw-dpo
```
