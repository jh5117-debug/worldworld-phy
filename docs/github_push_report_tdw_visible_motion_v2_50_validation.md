# GitHub Push Report: TDW visible-motion v2 50 Validation

Branch:

`physion-tdw-visible-motion-v2-50-validation`

Commit message:

`Run visible-motion v2 TDW 50-sample validation`

Local commit:

Recorded as the branch `HEAD` for `physion-tdw-visible-motion-v2-50-validation`; see the final report for the exact hash from this run.

Remote:

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

Push status:

Not completed from the local sandbox in this run.

Reason:

- direct local `git push` failed because sandbox DNS/network access could not resolve `ssh.github.com`;
- the required network escalation for local `git push` was rejected;
- the commit patch was transferred to the TDW host with `scp`, but follow-up remote git operations timed out / hung before a confirmed remote push.

Prepared scope:

- `docs/*.md`
- TDW generation v2 Python files only if modified

Excluded from Git:

- `local_assets/`
- generated HDF5 / H5
- generated MP4
- NPY / NPZ
- large logs
- weights / checkpoints / LoRA / latents

No generated assets are committed.
