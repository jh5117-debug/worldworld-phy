# Stage A 1000 prompt_v2 Sampler Dry-run Report

## Sampler

- sampler: balanced
- balance keys: template,camera_variant
- shuffle seed: 123
- max dry-run steps: 200

## Coverage

- first 20 templates: see local sampler_summary.json
- first 60 templates: see local sampler_summary.json
- all dry-run templates: see local sampler_summary.json
- duplicate sample count: see local sampler_summary.json

The actual 300-step run confirmed balanced coverage exactly: drop 75, collision 75, roll 75, containment 75, with first20 = 5/5/5/5.
