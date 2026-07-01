Current Status:
BLOCKED

# Winner-Anchor-Only 1-Pair v8b

Decision: `WINNER_ANCHOR_1PAIR_FAIL_OOM`

- Pair manifest: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Objective: `winner_anchor_only`
- Requested steps: 5
- Completed steps: 1
- Runtime status: FAILED
- Finite: False
- Nonzero grad: True
- Save/load OK: False
- Trainable params: 6553600
- Final winner improvement: 0.0
- Mean winner improvement: 0.0
- Final objective loss: 0.15119405090808868
- Error: `OutOfMemoryError('CUDA out of memory. Tried to allocate 1.25 GiB. GPU 0 has a total capacity of 95.09 GiB of which 1.11 GiB is free. Including non-PyTorch memory, this process has 93.96 GiB memory in use. Of the allocated memory 89.93 GiB is allocated by PyTorch, and 3.53 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://docs.pytorch.org/docs/stable/notes/cuda.html#optimizing-memory-usage-with-pytorch-cuda-alloc-conf)')`

The run did not satisfy the winner-preserving gate. It completed one optimizer step, then hit CUDA OOM before finishing 5 steps. Because winner improvement was not positive and the run was not finite, 10-pair winner-anchor and SDPO/Linear variants were not run.
