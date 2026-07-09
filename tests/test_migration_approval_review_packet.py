from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from cam_physgeo.orchestration.migration_approval_review_packet import build_review_rows, score_row, summarize, write_json


def _write_plan(path: Path) -> None:
    rows = [
        {
            "manifest_kind": "weights",
            "row_index": "1",
            "category": "weight_or_model_candidate",
            "manifest_path": "links/base_model",
            "resolved_target": "/models/LingBot/Wan/adapter",
            "copy_source": "/models/LingBot/Wan/adapter",
            "destination_subdir": "weights",
            "exists": "True",
            "file_type": "file",
            "size_bytes": "100",
            "sha256_status": "SHA256_OK",
            "sha256": "abc",
            "copy_recommendation": "REVIEW_BEFORE_COPY",
            "approved": "false",
            "approval_reason": "review",
            "copy_status": "NEEDS_REVIEW_FILE",
            "notes": "",
        },
        {
            "manifest_kind": "data",
            "row_index": "2",
            "category": "physeditworld_or_gravity_candidate",
            "manifest_path": "local_assets/old.mp4",
            "resolved_target": "local_assets/old.mp4",
            "copy_source": "local_assets/old.mp4",
            "destination_subdir": "data",
            "exists": "True",
            "file_type": "file",
            "size_bytes": "50",
            "sha256_status": "SHA256_OK",
            "sha256": "def",
            "copy_recommendation": "REVIEW",
            "approved": "false",
            "approval_reason": "review",
            "copy_status": "NEEDS_REVIEW_FILE",
            "notes": "",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_score_blocks_local_assets() -> None:
    priority, score, action, reason, safety = score_row({"copy_source": "local_assets/run/foo.mp4", "exists": "True"})
    assert priority == "blocked"
    assert action == "DO_NOT_APPROVE"
    assert "local_assets" in reason
    assert "policy" in safety


def test_review_packet_ranks_high_priority_weight(tmp_path: Path) -> None:
    plan = tmp_path / "plan.tsv"
    _write_plan(plan)
    rows = build_review_rows(plan)
    assert rows[0].manifest_kind == "weights"
    assert rows[0].review_priority == "high"
    assert rows[-1].review_priority == "blocked"
    summary = summarize(rows, top_n=1)
    assert summary["decision"] == "MIGRATION_APPROVAL_REVIEW_PACKET_READY"
    assert summary["high_priority_rows"] == 1
    out = tmp_path / "summary.json"
    write_json(summary, out)
    assert json.loads(out.read_text())["top_review_sources"][0]["manifest_kind"] == "weights"


if __name__ == "__main__":
    root = Path("/tmp/test_migration_approval_review_packet_direct")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    test_score_blocks_local_assets()
    test_review_packet_ranks_high_priority_weight(root)


def test_score_demotes_code_env_artifacts() -> None:
    priority, score, action, reason, safety = score_row({
        "manifest_kind": "weights",
        "copy_source": "/repo/code/lingbot-world/wan/modules/t5.py",
        "exists": "True",
        "file_type": "file",
        "copy_status": "NEEDS_REVIEW_FILE",
    })
    assert priority == "low"
    assert action == "KEEP_UNAPPROVED_UNLESS_NEEDED"
    assert "code/env/example" in reason


def test_score_keeps_checkpoint_payload_high() -> None:
    priority, score, action, reason, safety = score_row({
        "manifest_kind": "weights",
        "copy_source": "/repo/checkpoints/LingBot/model.safetensors",
        "exists": "True",
        "file_type": "file",
        "copy_status": "NEEDS_REVIEW_FILE",
        "sha256_status": "SHA256_OK",
    })
    assert priority == "high"
    assert action == "REVIEW_FOR_APPROVAL"
    assert "model payload marker" in reason


def test_score_blocks_old_dpo_logs() -> None:
    priority, score, action, reason, safety = score_row({
        "copy_source": "/home/project/Diffueraser_DPO_Log/old_run",
        "exists": "True",
        "file_type": "dir",
        "copy_status": "NEEDS_REVIEW_DIR",
    })
    assert priority == "blocked"
    assert action == "DO_NOT_APPROVE"
    assert "diffueraser_dpo_log" in reason


def test_score_demotes_videophy_false_positive() -> None:
    priority, score, action, reason, safety = score_row({
        "manifest_kind": "data",
        "copy_source": "/data/VIDEOPHY2/sports_action_camera.mp4",
        "exists": "True",
        "file_type": "file",
        "copy_status": "NEEDS_REVIEW_FILE",
    })
    assert priority == "low"
    assert action == "KEEP_UNAPPROVED_UNLESS_NEEDED"
