# NVIDIA Multi-display Xorg Setup Report

Status: blocked.

- DISPLAY=:8 is existing NVIDIA/GPU0 and was preserved.
- DISPLAY=:9-:13 are Mesa llvmpipe and must not be used for TDW GPU generation.
- DISPLAY=:20-:26 are unavailable before root setup.
- GPU6 DISPLAY=:25 setup could not be attempted because root SSH/sudo is not available non-interactively.
- Root credential was not recorded.

Ready for multi-display TDW smoke: no.
