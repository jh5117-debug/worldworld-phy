"""Python entrypoint for the TDW multidisplay generation shell runner."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TDW generation chunks across multiple Xorg displays.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out_root", default="local_assets/data/physion/generated_v5")
    parser.add_argument("--displays", required=True)
    parser.add_argument("--profile", default="warmup_visible_motion_v5_aggressive_2x_demo")
    parser.add_argument("--chunk_size", default="2")
    parser.add_argument("--validate_each_chunk", default="false")
    parser.add_argument("--stop_on_chunk_failure_rate", default="0.10")
    parser.add_argument("--reject_llvpipe", default="true")
    parser.add_argument("--no_overwrite", action="store_true")
    args = parser.parse_args()

    script = Path("scripts/34_run_tdw_multidisplay_generation.sh")
    if not script.exists():
        raise SystemExit(f"missing runner script: {script}")
    cmd = [
        "bash", str(script),
        "--manifest", args.manifest,
        "--out_root", args.out_root,
        "--displays", args.displays,
        "--profile", args.profile,
        "--chunk_size", str(args.chunk_size),
        "--validate_each_chunk", args.validate_each_chunk,
        "--stop_on_chunk_failure_rate", args.stop_on_chunk_failure_rate,
        "--reject_llvpipe", args.reject_llvpipe,
    ]
    if args.no_overwrite:
        cmd.append("--no_overwrite")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
