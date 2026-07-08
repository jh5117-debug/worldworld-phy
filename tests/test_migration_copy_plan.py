from pathlib import Path

from cam_physgeo.orchestration.migration_copy_plan import build_plan_rows, summarize


def test_copy_plan_defaults_to_not_approved(tmp_path: Path):
    payload = tmp_path / "payload.txt"
    payload.write_text("x", encoding="utf-8")
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "category\tpath\tresolved_target\texists\tfile_type\tsize_bytes\tmtime\tsha256_status\tsha256\tcopy_recommendation\tnotes\n"
        f"test\t{payload}\t\tTrue\tfile\t1\t\tSHA256_OK\tabc\tREVIEW\tunit\n",
        encoding="utf-8",
    )
    rows = build_plan_rows("data", manifest)
    assert rows[0].approved == "false"
    assert rows[0].copy_status == "NEEDS_REVIEW_FILE"


def test_copy_plan_summary_requires_review(tmp_path: Path):
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "category\tpath\tresolved_target\texists\tfile_type\tsize_bytes\tmtime\tsha256_status\tsha256\tcopy_recommendation\tnotes\n",
        encoding="utf-8",
    )
    summary = summarize(build_plan_rows("weights", manifest))
    assert summary["decision"] == "COPY_PLAN_REVIEW_REQUIRED"
    assert summary["approved_rows"] == 0
