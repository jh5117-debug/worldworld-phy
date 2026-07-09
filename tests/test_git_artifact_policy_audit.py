from cam_physgeo.orchestration.git_artifact_policy_audit import classify_artifacts, decide, parse_ls_tree


def test_parse_ls_tree_extracts_path_and_size():
    out = "100644 blob abc 123\tfoo/bar.txt\n100644 blob def -\tsubmodule\n"
    assert parse_ls_tree(out) == [("foo/bar.txt", 123), ("submodule", 0)]


def test_classify_blocks_forbidden_extensions():
    rows = classify_artifacts([("train.log", 10), ("local_assets/x.txt", 1)])
    assert len(rows) == 2
    assert all(row.status == "BLOCKED_FORBIDDEN_TRACKED_ARTIFACT" for row in rows)
    assert decide(rows) == "GIT_ARTIFACT_POLICY_BLOCKED_FORBIDDEN_TRACKED_ARTIFACTS"


def test_classify_warns_large_non_forbidden_file():
    rows = classify_artifacts([("third_party/data.csv", 20 * 1024 * 1024)])
    assert rows[0].status == "WARN_LARGE_TRACKED_FILE"
    assert decide(rows) == "GIT_ARTIFACT_POLICY_PASS_WITH_SIZE_WARNINGS"


def test_decide_passes_clean_rows():
    assert decide([]) == "GIT_ARTIFACT_POLICY_PASS"
