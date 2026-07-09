from cam_physgeo.orchestration.physeditworld_external_state_watch import WatchRow, derive_decision, split_roots


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_decision_waits_for_nas_first():
    rows = [WatchRow("nas_target", "BLOCKED", "missing"), WatchRow("physeditworld_roots_env", "PASS", "ok")]
    assert derive_decision(rows) == "PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_NAS"


def test_decision_waits_for_root_env_after_nas():
    rows = [WatchRow("nas_target", "PASS", "ok"), WatchRow("physeditworld_roots_env", "BLOCKED", "unset")]
    assert derive_decision(rows) == "PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_ROOT_ENV"
