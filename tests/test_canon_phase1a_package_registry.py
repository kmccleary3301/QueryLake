from __future__ import annotations

import json

from QueryLake.canon.package import (
    build_route_graph_package_bundle,
    load_graph_package_registry,
    register_graph_package_bundle,
    resolve_selected_graph_package,
)
from QueryLake.canon.control.pointer_registry import save_pointer_registry


def _build_bundle(route: str, revision: str) -> dict:
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    return build_route_graph_package_bundle(route=route, package_revision=revision)


def test_register_graph_package_bundle_and_route_index(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    bundle_a = _build_bundle("search_bm25.document_chunk", "rev-a")
    bundle_b = _build_bundle("search_file_chunks", "rev-b")

    register_graph_package_bundle(bundle=bundle_a, registry_path=registry_path)
    registry = register_graph_package_bundle(bundle=bundle_b, registry_path=registry_path)

    assert registry["schema_version"] == "canon_graph_package_registry_v1"
    assert len(registry["packages"]) == 2
    assert "search_bm25.document_chunk" in registry["route_index"]
    assert "search_file_chunks" in registry["route_index"]


def test_resolve_selected_graph_package_uses_pointer_bindings(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle_a = _build_bundle("search_bm25.document_chunk", "rev-a")
    bundle_b = _build_bundle("search_file_chunks", "rev-b")
    register_graph_package_bundle(bundle=bundle_a, registry_path=registry_path)
    register_graph_package_bundle(bundle=bundle_b, registry_path=registry_path)

    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-19T00:00:00+00:00",
            "shadow_pointer": {
                "pointer_id": "ptr-shadow",
                "graph_id": bundle_a["graph"]["graph_id"],
                "package_revision": "rev-a",
                "profile_id": "aws_aurora_pg_opensearch_v1",
                "route_ids": ["search_bm25.document_chunk", "search_file_chunks"],
                "mode": "shadow",
                "metadata": {
                    "package_bindings": {
                        "search_bm25.document_chunk": {
                            "package_id": bundle_a["package_id"],
                            "package_revision": "rev-a",
                            "graph_id": bundle_a["graph"]["graph_id"],
                        },
                        "search_file_chunks": {
                            "package_id": bundle_b["package_id"],
                            "package_revision": "rev-b",
                            "graph_id": bundle_b["graph"]["graph_id"],
                        },
                    }
                },
            },
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        },
        pointer_registry_path,
    )

    selected = resolve_selected_graph_package(
        registry=load_graph_package_registry(registry_path),
        pointer_registry=json.loads(pointer_registry_path.read_text()),
        route_id="search_file_chunks",
        profile_id="aws_aurora_pg_opensearch_v1",
        mode="shadow",
    )

    assert selected["resolved"] is True
    assert selected["package"]["route_id"] == "search_file_chunks"
    assert selected["package"]["package_revision"] == "rev-b"


def test_resolve_selected_graph_package_falls_back_to_shadow_when_candidate_missing(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    bundle = _build_bundle("search_bm25.document_chunk", "rev-a")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    pointer_registry = {
        "schema_version": "canon_pointer_registry_v1",
        "generated_at": "2026-04-19T00:00:00+00:00",
        "shadow_pointer": {
            "pointer_id": "ptr-shadow",
            "graph_id": bundle["graph"]["graph_id"],
            "package_revision": bundle["package_revision"],
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "route_ids": ["search_bm25.document_chunk"],
            "mode": "shadow",
            "metadata": {},
        },
        "candidate_primary_pointer": {
            "pointer_id": "ptr-candidate",
            "graph_id": "missing-graph",
            "package_revision": "missing-rev",
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "route_ids": ["search_bm25.document_chunk"],
            "mode": "candidate_primary",
            "metadata": {},
        },
        "primary_pointer": None,
        "history": [],
    }

    selected = resolve_selected_graph_package(
        registry=load_graph_package_registry(registry_path),
        pointer_registry=pointer_registry,
        route_id="search_bm25.document_chunk",
        profile_id="aws_aurora_pg_opensearch_v1",
        mode="candidate_primary",
    )

    assert selected["resolved"] is True
    assert selected["pointer_slot"] == "shadow_pointer"
    assert len(selected["evaluated_pointers"]) == 2
