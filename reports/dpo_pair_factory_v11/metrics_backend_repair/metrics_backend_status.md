Current Status: PASS_WITH_SCOPE_CAVEATS

# Metrics Backend Status After Repaired Ready500 Verification

- LPIPS: REAL_SMOKE_PASS. Real `LPIPS(net=alex)` produced numeric winner-vs-loser values for 10 repaired canonical pairs.
- VBench: REAL_SMOKE_PASS for `temporal_flickering` on 3 videos. This verifies one real VBench scoring path, not the full suite.
- FVD: REAL_I3D_BACKEND_SMOKE_PASS. A local TorchScript I3D weight was found and a corrected-layout 4-pair FVD smoke ran successfully. This is backend verification, not a stable benchmark score.
- Image FID: installed/importable, but remains diagnostic only and is not reported as FVD.

Environment caveat: VBench installation added user-site `transformers==4.33.2`, while fastwam expects `transformers==4.49.0`. Future training/rollout should isolate or pin environments.
