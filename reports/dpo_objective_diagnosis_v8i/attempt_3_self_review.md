Current Status:
T5_FAST_INIT_VALIDATED

# v8i Attempt 3 Self Review

- Plan: isolate T5 load.
- Actual: no-random-init alone still exceeded the strict 180s stage, but extended run showed T5 construction, checkpoint load, and state_dict injection are valid.
- Follow-up: patch default parameter reset for Linear/Embedding/LayerNorm before checkpoint-covered UMT5 construction.
- Result: fast-init T5 construction dropped to about 20.7s; checkpoint load and state_dict injection remained valid.
- User intervention required: no.
