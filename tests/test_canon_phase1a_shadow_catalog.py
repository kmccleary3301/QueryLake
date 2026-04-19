import json

from QueryLake.canon.runtime import (
    apply_shadow_retention_plan,
    build_shadow_artifact_catalog,
    build_shadow_retention_plan,
    load_shadow_artifacts,
    persist_shadow_artifact_catalog,
    persist_shadow_retention_plan,
)


def test_shadow_artifact_catalog_correlates_reports_bundles_and_traces(tmp_path):
    (tmp_path / "canon-shadow-case1.json").write_text(
        json.dumps(
            {
                "schema_version": "canon_shadow_report_v1",
                "report_id": "canon-shadow-case1",
                "generated_at": "2026-04-19T00:00:00+00:00",
                "route": "search_bm25.document_chunk",
                "shadow_diff": {"divergence_class": "exact_match"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "canon-shadow-bundle-case1.json").write_text(
        json.dumps(
            {
                "schema_version": "canon_shadow_replay_bundle_v1",
                "bundle_id": "canon-shadow-bundle-case1",
                "generated_at": "2026-04-19T00:00:01+00:00",
                "route": "search_bm25.document_chunk",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "canon-shadow-traces-case1.json").write_text(
        json.dumps(
            {
                "schema_version": "canon_shadow_trace_export_v1",
                "export_id": "canon-shadow-traces-case1",
                "generated_at": "2026-04-19T00:00:02+00:00",
                "route": "search_bm25.document_chunk",
            }
        ),
        encoding="utf-8",
    )

    artifacts = load_shadow_artifacts(tmp_path)
    catalog = build_shadow_artifact_catalog(artifacts)

    assert catalog["artifact_count"] == 3
    assert catalog["counts"]["report"] == 1
    assert catalog["counts"]["replay_bundle"] == 1
    assert catalog["counts"]["trace_export"] == 1
    assert catalog["orphan_correlation_keys"] == []
    assert "shadow_artifacts_structurally_complete" in catalog["recommendations"]


def test_shadow_retention_plan_prunes_older_route_runs_and_can_apply(tmp_path):
    for suffix, generated_at in [("old", "2026-04-18T00:00:00+00:00"), ("new", "2026-04-19T00:00:00+00:00")]:
        (tmp_path / f"canon-shadow-{suffix}.json").write_text(
            json.dumps(
                {
                    "schema_version": "canon_shadow_report_v1",
                    "report_id": f"canon-shadow-{suffix}",
                    "generated_at": generated_at,
                    "route": "search_file_chunks",
                    "shadow_diff": {"divergence_class": "exact_match"},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / f"canon-shadow-bundle-{suffix}.json").write_text(
            json.dumps(
                {
                    "schema_version": "canon_shadow_replay_bundle_v1",
                    "bundle_id": f"canon-shadow-bundle-{suffix}",
                    "generated_at": generated_at,
                    "route": "search_file_chunks",
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / f"canon-shadow-traces-{suffix}.json").write_text(
            json.dumps(
                {
                    "schema_version": "canon_shadow_trace_export_v1",
                    "export_id": f"canon-shadow-traces-{suffix}",
                    "generated_at": generated_at,
                    "route": "search_file_chunks",
                }
            ),
            encoding="utf-8",
        )

    artifacts = load_shadow_artifacts(tmp_path)
    plan = build_shadow_retention_plan(artifacts, keep_latest_per_route=1)
    assert plan["prune_count"] == 3
    assert any(path.endswith("canon-shadow-old.json") for path in plan["prune_paths"])

    persisted_catalog = persist_shadow_artifact_catalog(
        catalog=build_shadow_artifact_catalog(artifacts),
        output_path=tmp_path / "artifact-catalog.json",
    )
    persisted_plan = persist_shadow_retention_plan(
        plan=plan,
        output_path=tmp_path / "retention-plan.json",
    )
    assert persisted_catalog.endswith("artifact-catalog.json")
    assert persisted_plan.endswith("retention-plan.json")

    dry_run = apply_shadow_retention_plan(plan, dry_run=True)
    assert dry_run["removed_count"] == 0

    applied = apply_shadow_retention_plan(plan, dry_run=False)
    assert applied["removed_count"] == 3
    assert not (tmp_path / "canon-shadow-old.json").exists()
