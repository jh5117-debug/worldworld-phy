# TDW Multidisplay Scaleup Plan Report

Status: planned, not executed.

Current dataset audit confirms the v5 1000 dataset exists and is structurally valid. Because multidisplay NVIDIA Xorg setup is not ready, this run did not generate additional TDW data.

After display setup and 16-sample smoke pass:

- If current 1000 remains accepted, generate the next 1000 samples first, not 4000.
- Use v5 aggressive profile.
- Use unique start indices and seed ranges after the current max.
- Use `combined_prompt_v2` for downstream prompt manifests and rollout inputs.
- Validate and convert each generated batch before merging.
- Stop if duplicate scene hashes or chunk failure rates become systematic.

Do not expand toward 5000 until the first additional 1000 passes validation, conversion, manifest/split audit, and review-pack sampling.
