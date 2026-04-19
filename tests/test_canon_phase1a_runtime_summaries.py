from QueryLake.canon.runtime import build_replay_summary, build_trace_summary


def test_trace_summary_builder_emits_phase1a_compile_shape():
    payload = build_trace_summary(retention_class="summary_plus_detail", execution_mode="canon_shadow").to_payload()

    assert payload["available"] is True
    assert payload["retention_class"] == "summary_plus_detail"
    assert payload["execution_mode"] == "canon_shadow"
    assert payload["span_model"] == "phase1a_bridge_compile_only"


def test_replay_summary_builder_marks_debug_replay_as_available():
    payload = build_replay_summary(
        retention_class="debug_replay",
        replay_guarantee_class="analysis_only",
    ).to_payload()

    assert payload["available"] is True
    assert payload["retention_class"] == "debug_replay"
    assert payload["replay_guarantee_class"] == "analysis_only"
