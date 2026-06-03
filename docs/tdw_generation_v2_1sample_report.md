# TDW Generation v2 1-Sample Report

Status: blocked before actual TDW/Unity generation.

Reason: the existing upstream batch runner does not expose an explicit mild-only camera set. Running it directly for `warmup_mild` could leak stress/reobserve variants into the warmup split. The v2 wrapper therefore records the command and blocks actual warmup generation until mild-only selection is guaranteed.

No HDF5/video was generated in this stage. This is not a fake success.
