Current Status:
PASS_DIAGNOSTIC_NO_TRAINING

# v8c Winner-Anchor Memory Audit

- Separate reference model loaded: no.
- Reference in training graph: no; reference energy is no_grad with LoRA scaling zero.
- Loser branch loaded: no.
- Cached winner input used: yes.
- Used window frames: 81.
- Backward/optimizer stages: skipped in this no-training audit and measured by the runner.
- Preliminary conclusion: v8c removes the separate reference and loser branches; remaining risk is policy forward/backward activation cost.
