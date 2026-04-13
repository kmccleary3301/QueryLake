from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_profile_bootstrap import main


class _FakeDatabase:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_profile_bootstrap_script_emits_report(monkeypatch, tmp_path):
    fake_database = _FakeDatabase()
    captured = {}

    def fake_initialize_database_engine():
        return fake_database

    def fake_bootstrap_profile_projections(*, database, profile, projection_ids, metadata_store_path):
        captured["database"] = database
        captured["profile_id"] = profile.id
        captured["projection_ids"] = list(projection_ids or [])
        captured["metadata_store_path"] = metadata_store_path

        class _Report:
            def model_dump(self):
                return {
                    "profile_id": profile.id,
                    "projection_ids": ["document_chunk_lexical_projection_v1"],
                    "projection_items": [{
                        "projection_id": "document_chunk_lexical_projection_v1",
                        "status_before": "absent",
                        "status_after": "ready",
                        "executed_action_count": 1,
                        "skipped_action_count": 0,
                        "lifecycle_outcome": "materialized_from_absent",
                        "materialization_target": {
                            "authority_model": "document_chunk_compatibility",
                            "source_scope": "document_chunk",
                            "target_backend_name": "opensearch",
                        },
                    }],
                    "ready_projection_ids": ["document_chunk_lexical_projection_v1"],
                    "building_projection_ids": [],
                    "stale_projection_ids": [],
                    "failed_projection_ids": [],
                    "absent_projection_ids": [],
                    "metadata": {
                        "ready_count": 1,
                        "executed_action_count": 1,
                        "skipped_action_count": 0,
                        "lifecycle_outcome_counts": {"materialized_from_absent": 1},
                    },
                }

        return _Report()

    bringup_call_count = {"count": 0}

    def fake_build_profile_bringup_payload(*, profile, metadata_store_path):
        bringup_call_count["count"] += 1
        return {
            "profile": {"id": profile.id},
            "summary": {
                "boot_ready": bringup_call_count["count"] > 1,
                "configuration_ready": True,
                "route_runtime_ready": bringup_call_count["count"] > 1,
                "backend_connectivity_ready": True,
                "ready_projection_count": 0 if bringup_call_count["count"] == 1 else 1,
                "runtime_ready_route_count": 0 if bringup_call_count["count"] == 1 else 1,
            },
            "ready_projection_ids": [] if bringup_call_count["count"] == 1 else ["document_chunk_lexical_projection_v1"],
            "route_runtime_ready_ids": [] if bringup_call_count["count"] == 1 else ["search_bm25.document_chunk"],
            "route_runtime_blocked_ids": ["search_bm25.document_chunk"] if bringup_call_count["count"] == 1 else [],
            "projection_ids_needing_build": ["document_chunk_lexical_projection_v1"] if bringup_call_count["count"] == 1 else [],
            "backend_unreachable_planes": [],
        }

    monkeypatch.setattr(
        "scripts.db_compat_profile_bootstrap.initialize_database_engine",
        fake_initialize_database_engine,
    )
    monkeypatch.setattr(
        "scripts.db_compat_profile_bootstrap.bootstrap_profile_projections",
        fake_bootstrap_profile_projections,
    )
    monkeypatch.setattr(
        "scripts.db_compat_profile_bootstrap.build_profile_bringup_payload",
        fake_build_profile_bringup_payload,
    )

    output_path = tmp_path / "bootstrap_report.json"
    assert (
        main(
            [
                "--profile",
                "aws_aurora_pg_opensearch_v1",
                "--projection-id",
                "document_chunk_lexical_projection_v1",
                "--projection-metadata-path",
                str(tmp_path / "projection_meta.json"),
                "--output",
                str(output_path),
                "--validate-runtime-ready",
                "--expect-boot-ready",
                "true",
                "--expect-configuration-ready",
                "true",
                "--expect-route-runtime-ready",
                "true",
                "--expect-backend-connectivity-ready",
                "true",
                "--expect-executed-action-count",
                "1",
                "--expect-skipped-action-count",
                "0",
                "--expect-projection-status",
                "document_chunk_lexical_projection_v1=ready",
            ]
        )
        == 0
    )

    assert captured["database"] is fake_database
    assert captured["profile_id"] == "aws_aurora_pg_opensearch_v1"
    assert captured["projection_ids"] == ["document_chunk_lexical_projection_v1"]
    assert fake_database.closed is True
    payload = output_path.read_text(encoding="utf-8")
    assert '"ready_count": 1' in payload
    assert '"boot_ready": true' in payload
    assert '"target_backend_name": "opensearch"' in payload
    assert '"bootstrap_delta"' in payload
    assert '"boot_ready_before": false' in payload
    assert '"boot_ready_after": true' in payload
    assert '"bootstrap_improved_runtime_readiness": true' in payload
    assert '"projection_ids_recovered": [' in payload
    assert '"lifecycle_outcome": "materialized_from_absent"' in payload
    assert '"lifecycle_outcome_counts"' in payload


def test_profile_bootstrap_script_supports_status_assertions(monkeypatch, tmp_path):
    fake_database = _FakeDatabase()

    def fake_initialize_database_engine():
        return fake_database

    def fake_bootstrap_profile_projections(*, database, profile, projection_ids, metadata_store_path):
        class _Report:
            def model_dump(self):
                return {
                    "profile_id": profile.id,
                    "projection_ids": ["document_chunk_lexical_projection_v1"],
                    "projection_items": [{
                        "projection_id": "document_chunk_lexical_projection_v1",
                        "status_before": "ready",
                        "status_after": "stale",
                        "executed_action_count": 0,
                        "skipped_action_count": 1,
                        "lifecycle_outcome": "stale",
                    }],
                    "ready_projection_ids": [],
                    "building_projection_ids": [],
                    "stale_projection_ids": ["document_chunk_lexical_projection_v1"],
                    "failed_projection_ids": [],
                    "absent_projection_ids": [],
                    "metadata": {
                        "ready_count": 0,
                        "executed_action_count": 0,
                        "skipped_action_count": 1,
                        "lifecycle_outcome_counts": {"stale": 1},
                    },
                }

        return _Report()

    monkeypatch.setattr(
        "scripts.db_compat_profile_bootstrap.initialize_database_engine",
        fake_initialize_database_engine,
    )
    monkeypatch.setattr(
        "scripts.db_compat_profile_bootstrap.bootstrap_profile_projections",
        fake_bootstrap_profile_projections,
    )

    assert (
        main(
            [
                "--profile",
                "aws_aurora_pg_opensearch_v1",
                "--expect-executed-action-count",
                "0",
                "--expect-skipped-action-count",
                "1",
                "--expect-projection-status",
                "document_chunk_lexical_projection_v1=stale",
            ]
        )
        == 0
    )
    assert fake_database.closed is True
