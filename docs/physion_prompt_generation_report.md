# Physion Prompt Generation Report

Implemented files:

- `cam_physgeo/data/prompt_templates.py`
- `cam_physgeo/data/physion_prompt_builder.py`

Prompt generation is deterministic and metadata-based. It does not include action labels and does not leak the ground-truth outcome. The converter writes `prompt.txt` for every LingBot cam-only sample.
