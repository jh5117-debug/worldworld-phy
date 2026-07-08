from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


@dataclass
class AuditItem:
    name: str
    path: str
    status: str
    command: str = ""
    notes: str = ""


CORE_FILES = {
    "h20_hostname.txt",
    "migration_date.txt",
    "git_status_short.txt",
    "git_branch.txt",
    "git_log_30.txt",
    "df_h20_pai.txt",
    "repo_du_summary.txt",
    "python_version.txt",
    "python_path.txt",
    "torch_cuda_info.txt",
    "untracked_large_files.tsv",
}

OPTIONAL_FILES = {
    "environment_no_builds.yml",
    "pip_freeze.txt",
    "nvidia_smi.txt",
}


def run_capture(cmd: Sequence[str], out_path: Path, timeout: int = 60, env: dict[str, str] | None = None) -> AuditItem:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    printable = " ".join(shlex.quote(x) for x in cmd)
    try:
        proc = subprocess.run(
            list(cmd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            env=env,
        )
        output = proc.stdout or ""
        if proc.returncode != 0 and not output:
            output = f"command exited with code {proc.returncode}\n"
        out_path.write_text(output, encoding="utf-8", errors="ignore")
        status = "PASS" if proc.returncode == 0 else "WARN"
        notes = "" if proc.returncode == 0 else f"exit_code={proc.returncode}"
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", "ignore")
        out_path.write_text(str(output) + f"\nTIMEOUT after {timeout}s\n", encoding="utf-8", errors="ignore")
        status = "WARN"
        notes = f"timeout={timeout}s"
    except Exception as exc:  # pragma: no cover - defensive runtime capture
        out_path.write_text(f"ERROR: {exc!r}\n", encoding="utf-8", errors="ignore")
        status = "WARN"
        notes = repr(exc)
    return AuditItem(out_path.stem, str(out_path), status, printable, notes)


def write_text_item(name: str, value: str, out_dir: Path) -> AuditItem:
    path = out_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")
    return AuditItem(path.stem, str(path), "PASS")


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0 or unit == "TB":
            return f"{value:.2f}{unit}"
        value /= 1024.0
    return f"{value:.2f}TB"


def collect_untracked_large_files(repo: Path, out_path: Path, threshold_mb: int) -> AuditItem:
    threshold = threshold_mb * 1024 * 1024
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str | int]] = []
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            out_path.write_text("path\tsize_bytes\tsize_human\tnotes\n", encoding="utf-8")
            return AuditItem(out_path.stem, str(out_path), "WARN", "git ls-files --others --exclude-standard -z", proc.stderr.decode("utf-8", "ignore")[-500:])
        for raw in proc.stdout.split(b"\0"):
            if not raw:
                continue
            rel = raw.decode("utf-8", "ignore")
            path = repo / rel
            try:
                if path.is_file():
                    size = path.stat().st_size
                else:
                    continue
            except OSError:
                continue
            if size >= threshold:
                rows.append({"path": rel, "size_bytes": size, "size_human": human_size(size), "notes": "untracked_large"})
        rows.sort(key=lambda r: int(r["size_bytes"]), reverse=True)
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "size_bytes", "size_human", "notes"], delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return AuditItem(out_path.stem, str(out_path), "PASS", "git ls-files --others --exclude-standard -z", f"large_untracked_count={len(rows)} threshold_mb={threshold_mb}")
    except Exception as exc:  # pragma: no cover - defensive runtime capture
        out_path.write_text("path\tsize_bytes\tsize_human\tnotes\n", encoding="utf-8")
        return AuditItem(out_path.stem, str(out_path), "WARN", "git ls-files --others --exclude-standard -z", repr(exc))


def collect_torch_cuda_info(out_path: Path) -> AuditItem:
    code = """
import sys
print('python', sys.version)
try:
    import torch
    print('torch', torch.__version__)
    print('cuda', torch.version.cuda)
    print('cuda_available', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('device_count', torch.cuda.device_count())
        for i in range(torch.cuda.device_count()):
            print(i, torch.cuda.get_device_name(i))
except Exception as e:
    print('torch_import_error', repr(e))
""".strip()
    return run_capture([sys.executable, "-c", code], out_path, timeout=60)


def decision_for(items: list[AuditItem], out_dir: Path) -> str:
    existing = {Path(item.path).name for item in items if Path(item.path).exists()}
    missing_core = sorted(CORE_FILES - existing)
    if missing_core:
        return "MIGRATION_AUDIT_BUNDLE_INCOMPLETE"
    return "MIGRATION_AUDIT_BUNDLE_READY"


def write_summary(items: list[AuditItem], decision: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    lines = [
        "# H20 Migration Audit Bundle",
        "",
        f"Decision: `{decision}`",
        "",
        "## Status Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## Files", ""])
    for item in items:
        lines.append(f"- `{item.name}`: `{item.status}` -> `{item.path}`")
        if item.command:
            lines.append(f"  - command: `{item.command}`")
        if item.notes:
            lines.append(f"  - notes: {item.notes}")
    lines.extend([
        "",
        "## Safety",
        "",
        "- CPU/IO-only audit; no file copy, no deletion, no rsync execute.",
        "- `nvidia-smi` is query-only; no GPU jobs are launched.",
        "- `untracked_large_files.tsv` records large untracked files for operator review but does not delete them.",
    ])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect(repo: Path, out_dir: Path, threshold_mb: int) -> tuple[str, list[AuditItem]]:
    items: list[AuditItem] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    items.append(write_text_item("h20_hostname.txt", socket.gethostname(), out_dir))
    items.append(write_text_item("migration_date.txt", datetime.now(timezone.utc).astimezone().isoformat(), out_dir))
    items.append(run_capture(["git", "status", "--short"], out_dir / "git_status_short.txt", timeout=60))
    items.append(run_capture(["git", "branch", "--show-current"], out_dir / "git_branch.txt", timeout=30))
    items.append(run_capture(["git", "log", "--oneline", "--decorate", "-30"], out_dir / "git_log_30.txt", timeout=60))
    items.append(run_capture(["df", "-h", "/home/nvme03", "/home/nvme04", "/mnt/workspace/hj/nas_hj"], out_dir / "df_h20_pai.txt", timeout=60))
    items.append(run_capture(["du", "-sh", ".", "docs", "reports", "manifests", "configs", "cam_physgeo", "src"], out_dir / "repo_du_summary.txt", timeout=180))
    conda = shutil.which("conda")
    if conda:
        items.append(run_capture([conda, "env", "export", "--no-builds"], out_dir / "environment_no_builds.yml", timeout=180))
    else:
        path = out_dir / "environment_no_builds.yml"
        path.write_text("# conda not found in PATH; see pip_freeze.txt and python_path.txt\n", encoding="utf-8")
        items.append(AuditItem(path.stem, str(path), "WARN", "conda env export --no-builds", "conda_not_found"))
    items.append(run_capture([sys.executable, "-m", "pip", "freeze"], out_dir / "pip_freeze.txt", timeout=180))
    items.append(write_text_item("python_version.txt", sys.version.replace("\n", " "), out_dir))
    items.append(write_text_item("python_path.txt", sys.executable, out_dir))
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        items.append(run_capture([nvidia_smi], out_dir / "nvidia_smi.txt", timeout=20))
    else:
        path = out_dir / "nvidia_smi.txt"
        path.write_text("nvidia-smi not found\n", encoding="utf-8")
        items.append(AuditItem(path.stem, str(path), "WARN", "nvidia-smi", "nvidia_smi_not_found"))
    items.append(collect_torch_cuda_info(out_dir / "torch_cuda_info.txt"))
    items.append(collect_untracked_large_files(repo, out_dir / "untracked_large_files.tsv", threshold_mb))
    decision = decision_for(items, out_dir)
    return decision, items


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Collect CPU/IO-only H20 migration audit bundle")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--output_dir", default="reports/migration")
    ap.add_argument("--threshold_mb", type=int, default=50)
    ap.add_argument("--output_json", default="reports/migration/migration_audit_bundle.json")
    ap.add_argument("--summary", default="reports/migration/migration_audit_bundle.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).resolve()
    out_dir = Path(args.output_dir)
    decision, items = collect(repo, out_dir, args.threshold_mb)
    payload = {"decision": decision, "items": [asdict(item) for item in items]}
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(items, decision, Path(args.summary))
    print(json.dumps({"decision": decision, "items": len(items)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
