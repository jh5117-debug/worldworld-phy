# TDW Xorg Current Display Audit Before Fix

Root non-interactive SSH is unavailable in this session, so this audit was run as ubuntu and does not change Xorg.

| display | xdpyinfo | renderer | glxinfo excerpt |
| --- | --- | --- | --- |
| `:8` | OK | NVIDIA | `OpenGL vendor string: NVIDIA Corporation; OpenGL renderer string: NVIDIA H20/PCIe/SSE2; OpenGL version string: 4.6.0 NVIDIA 570.124.06` |
| `:9` | OK | llvmpipe | `OpenGL vendor string: Mesa; OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits); OpenGL version string: 4.5 (Compatibility Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3` |
| `:10` | OK | llvmpipe | `OpenGL vendor string: Mesa; OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits); OpenGL version string: 4.5 (Compatibility Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3` |
| `:11` | OK | llvmpipe | `OpenGL vendor string: Mesa; OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits); OpenGL version string: 4.5 (Compatibility Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3` |
| `:12` | OK | llvmpipe | `OpenGL vendor string: Mesa; OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits); OpenGL version string: 4.5 (Compatibility Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3` |
| `:13` | OK | llvmpipe | `OpenGL vendor string: Mesa; OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits); OpenGL version string: 4.5 (Compatibility Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3` |
| `:14` | FAIL | unavailable | `` |
| `:15` | FAIL | unavailable | `` |
| `:20` | FAIL | unavailable | `` |
| `:21` | FAIL | unavailable | `` |
| `:22` | FAIL | unavailable | `` |
| `:23` | FAIL | unavailable | `` |
| `:24` | FAIL | unavailable | `` |
| `:25` | FAIL | unavailable | `` |
| `:26` | FAIL | unavailable | `` |

Root credential was not recorded. DISPLAY=:8 was preserved.
