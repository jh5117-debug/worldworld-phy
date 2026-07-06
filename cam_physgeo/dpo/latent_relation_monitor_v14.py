
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
from fnmatch import fnmatch
from pathlib import Path

CANDIDATE_IMPORTS = ["vjepa", "vijepa", "dinov2", "transformers", "torchvision", "clip", "open_clip", "pytorchvideo"]
CANDIDATE_PATTERNS = ["*vjepa*", "*VJEPA*", "*videorepa*", "*VideoREPA*", "*videomae*", "*VideoMAE*", "*dinov2*", "*i3d*", "*trd*"]


def find_files(roots: list[str], max_hits: int = 200, max_dirs: int = 20000, max_seconds: float = 30.0) -> tuple[list[str], dict[str, object]]:
    hits: list[str] = []
    visited_dirs = 0
    started = time.time()
    stop_reason = "completed"
    skip_names = {".git", "node_modules", "__pycache__", "wandb", "runs"}
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            visited_dirs += 1
            dirnames[:] = [d for d in dirnames if d not in skip_names]
            if visited_dirs >= max_dirs:
                stop_reason = "max_dirs"
                break
            if time.time() - started > max_seconds:
                stop_reason = "max_seconds"
                break
            for name in filenames:
                lower = name.lower()
                if not any(fnmatch(name, pat) or fnmatch(lower, pat.lower()) for pat in CANDIDATE_PATTERNS):
                    continue
                path = Path(dirpath) / name
                try:
                    if path.stat().st_size > 0:
                        hits.append(str(path))
                except OSError:
                    continue
                if len(hits) >= max_hits:
                    stop_reason = "max_hits"
                    break
            if len(hits) >= max_hits or stop_reason != "completed":
                break
        if len(hits) >= max_hits or stop_reason != "completed":
            break
    meta = {"visited_dirs": visited_dirs, "elapsed_seconds": round(time.time() - started, 3), "stop_reason": stop_reason, "max_dirs": max_dirs, "max_seconds": max_seconds}
    return sorted(set(hits))[:max_hits], meta


def audit(args: argparse.Namespace) -> dict[str, object]:
    imports = {}
    for name in CANDIDATE_IMPORTS:
        imports[name] = importlib.util.find_spec(name) is not None
    files, search_meta = find_files(args.search_roots, max_dirs=int(args.max_dirs), max_seconds=float(args.max_seconds))
    has_teacher = any(imports.get(k, False) for k in ("vjepa", "vijepa", "dinov2", "clip", "open_clip")) and bool(files)
    decision = "LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING" if has_teacher else "LATENT_MONITOR_BLOCKED_BY_ENV"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"decision": decision, "imports": imports, "candidate_files": files[:100], "search_meta": search_meta, "note": "No model download attempted. Monitor only; no training."}
    (out_dir / "backend_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md = ["# Latent Relation Monitor Backend Audit", "", f"Decision: `{decision}`", "", f"Search meta: `{search_meta}`", "", "## Imports"]
    for k, v in imports.items():
        md.append(f"- {k}: {v}")
    md += ["", "## Candidate Local Files", ""]
    if files:
        md += [f"- `{p}`" for p in files[:50]]
    else:
        md.append("- none found")
    md += ["", "No V-JEPA / VideoREPA / TRD values are produced by this audit. If no backend is available, v14 must report `LATENT_MONITOR_BLOCKED`; fake latent scores are forbidden."]
    (out_dir / "backend_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--search_roots", nargs="+", default=["/home/nvme03", "/home/nvme04"])
    p.add_argument("--output_dir", default="reports/dpo_utility_calibration_v14/latent_monitor")
    p.add_argument("--max_dirs", type=int, default=20000)
    p.add_argument("--max_seconds", type=float, default=30.0)
    print(json.dumps(audit(p.parse_args(argv)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
