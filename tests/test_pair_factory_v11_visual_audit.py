from cam_physgeo.dpo.pair_factory_v11_visual_audit import audit_row

def test_audit_row_ready_for_local_visible():
    cs={"pair_id":"v11_SYN_1","status":"CONTACT_SHEET_PASS","failure_type":"local_patch_drift","source":"synthetic_controlled","pair_type":"TypeM"}
    score={"reward_margin":"0.2","mean_absdiff":"2","local_absdiff_mean":"20","local_absdiff_p95":"60","sharpness_ratio":"1.0","brightness":"120","contrast":"30"}
    row=audit_row(cs,score)
    assert row["reviewed"] is True
    assert row["human_visible"] is True
