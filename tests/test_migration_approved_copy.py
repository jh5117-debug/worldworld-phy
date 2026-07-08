from pathlib import Path

from cam_physgeo.orchestration.migration_approved_copy import build_rows, decision_for


def test_approved_copy_ignores_unapproved_rows(tmp_path: Path):
    plan = tmp_path / "plan.tsv"
    plan.write_text(
        "manifest_kind\trow_index\tcategory\tmanifest_path\tresolved_target\tcopy_source\tdestination_subdir\texists\tfile_type\tsize_bytes\tsha256_status\tsha256\tcopy_recommendation\tapproved\tapproval_reason\tcopy_status\tnotes\n"
        "data\t1\ttest\t/a\t\t/a\tdata\tFalse\tfile\t0\t\t\tREVIEW\tfalse\tneeds review\tNEEDS_REVIEW_FILE\tunit\n",
        encoding="utf-8",
    )
    rows = build_rows(plan, tmp_path / "dest")
    assert rows == []


def test_approved_copy_blocks_no_approved_rows(tmp_path: Path):
    assert decision_for([], tmp_path / "dest", execute=False) == "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS"


def test_approved_copy_rejects_local_assets(tmp_path: Path):
    source = tmp_path / "local_assets" / "x.txt"
    source.parent.mkdir()
    source.write_text("x", encoding="utf-8")
    plan = tmp_path / "plan.tsv"
    plan.write_text(
        "manifest_kind\trow_index\tcategory\tmanifest_path\tresolved_target\tcopy_source\tdestination_subdir\texists\tfile_type\tsize_bytes\tsha256_status\tsha256\tcopy_recommendation\tapproved\tapproval_reason\tcopy_status\tnotes\n"
        f"data\t1\ttest\t{source}\t\t{source}\tdata\tTrue\tfile\t1\t\t\tREVIEW\ttrue\tunit\tNEEDS_REVIEW_FILE\tunit\n",
        encoding="utf-8",
    )
    rows = build_rows(plan, tmp_path / "dest")
    assert rows[0].copy_status == "BLOCKED_LOCAL_ASSETS_EXCLUDED"
