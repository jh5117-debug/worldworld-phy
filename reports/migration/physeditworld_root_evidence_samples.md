# PhysEditWorld Root Evidence Sampler

Decision: `PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE`

## Status Counts

- `WAITING_FOR_FILLED_TEMPLATE`: 1

## Samples

- row `1` / `candidate_root`: `WAITING_FOR_FILLED_TEMPLATE`
  - error: candidate_root is empty or placeholder

## Safety

This sampler reads the filled root-submission TSV and bounded non-recursive evidence globs. It records example paths and sizes only. It does not copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO.
