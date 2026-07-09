# PhysEditWorld GPU Command Policy Audit

Decision: `PHYS_EDITWORLD_GPU_COMMAND_POLICY_PASS`

- Allowed physical GPUs: `4,5,6,7`
- Forbidden physical GPUs: `0,1,2,3`
- Scanned files: `44`
- CUDA_VISIBLE_DEVICES assignments: `0`
- Status counts: `{}`

This audit is CPU/IO only. It statically scans PhysEditWorld-related runnable artifacts for explicit CUDA_VISIBLE_DEVICES assignments and does not launch GPU work.
