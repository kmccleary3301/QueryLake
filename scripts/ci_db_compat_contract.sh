#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m py_compile \
  QueryLake/runtime/db_compat.py \
  QueryLake/runtime/retrieval_lanes.py \
  QueryLake/runtime/retrieval_lane_executors.py \
  QueryLake/runtime/opensearch_route_execution.py \
  QueryLake/runtime/opensearch_projection_writers.py \
  QueryLake/runtime/retrieval_adapter_interfaces.py \
  QueryLake/runtime/lexical_capability_planner.py \
  QueryLake/runtime/projection_contracts.py \
  QueryLake/runtime/projection_registry.py \
  QueryLake/runtime/projection_writers.py \
  QueryLake/runtime/projection_refresh.py \
  QueryLake/runtime/retrieval_route_executors.py \
  QueryLake/runtime/retrieval_explain.py \
  QueryLake/runtime/profile_bringup.py \
  QueryLake/runtime/local_dense_sidecar.py \
  QueryLake/runtime/local_profile_v2.py \
  QueryLake/runtime/local_route_execution.py \
  QueryLake/runtime/retrieval_primitive_factory.py \
  QueryLake/api/search.py \
  QueryLake/routing/api_call_router.py \
  QueryLake/runtime/service.py \
  QueryLake/database/create_db_session.py \
  server.py \
  scripts/db_compat_local_profile_completion_gate.py \
  scripts/db_compat_local_embedded_supported_slice_gate.py \
  scripts/db_compat_local_dense_sidecar_lifecycle_smoke.py \
  scripts/db_compat_local_profile_doctor.py \
  scripts/db_compat_v2_runtime_consistency.py \
  scripts/db_compat_v2_runtime_boundary_status.py \
  scripts/ci_db_compat_local_dense_sidecar_sync.py \
  scripts/ci_db_compat_v2_runtime_boundary_sync.py \
  scripts/ci_db_compat_local_profile_sync.py \
  scripts/db_compat_first_split_stack_completion_gate.py \
  scripts/db_compat_program_completion_gate.py \
  scripts/db_compat_v2_program_completion_gate.py \
  scripts/db_compat_profile_bringup_smoke.py \
  sdk/python/src/querylake_sdk/client.py \
  sdk/python/src/querylake_sdk/models.py \
  sdk/python/src/querylake_sdk/__init__.py

python scripts/ci_db_compat_profile_docs_sync.py
python scripts/ci_db_compat_capability_docs_sync.py
python scripts/ci_db_compat_supported_profiles_sync.py
python scripts/ci_local_profile_support_sync.py
python scripts/ci_db_compat_local_dense_sidecar_sync.py
python scripts/ci_db_compat_local_scope_expansion_sync.py
python scripts/ci_db_compat_v2_runtime_boundary_sync.py
python scripts/ci_db_compat_local_profile_sync.py
python scripts/ci_projection_descriptor_sync.py
python scripts/db_compat_contract_parity.py \
  --cases-json tests/fixtures/db_compat_contract_parity_cases.json \
  --output /tmp/querylake_db_compat_contract_parity.json \
  --min-split-executable-ratio 0.49
python scripts/db_compat_contract_parity.py \
  --cases-json tests/fixtures/db_compat_contract_parity_cases.json \
  --output /tmp/querylake_db_compat_contract_parity_ready_split.json \
  --enable-ready-split-stack-projections \
  --min-split-executable-ratio 0.49 \
  --min-split-runtime-ready-ratio 0.49 \
  --min-runtime-ready-overlap-ratio 0.49
python scripts/db_compat_profile_smoke.py \
  --profile paradedb_postgres_gold_v1 \
  --expect-boot-ready true \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --output /tmp/querylake_db_compat_profile_smoke_gold.json
python scripts/db_compat_profile_bringup_smoke.py \
  --profile paradedb_postgres_gold_v1 \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-ready-projection-count 0 \
  --output /tmp/querylake_db_compat_profile_bringup_gold.json
python scripts/db_compat_profile_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --expect-boot-ready false \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready false \
  --expect-declared-executable-routes-runtime-ready false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_bm25.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_file_chunks=projection_not_ready \
  --output /tmp/querylake_db_compat_profile_smoke_aws.json
python scripts/db_compat_profile_bringup_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --expect-boot-ready false \
  --expect-configuration-ready true \
  --expect-route-runtime-ready false \
  --expect-declared-executable-routes-runtime-ready false \
  --expect-ready-projection-count 0 \
  --expect-projection-needing-build document_chunk_lexical_projection_v1 \
  --expect-route-runtime search_hybrid.document_chunk=false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready \
  --output /tmp/querylake_db_compat_profile_bringup_aws.json
python scripts/db_compat_profile_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-route-implemented search_hybrid.document_chunk=true \
  --expect-route-implemented search_bm25.document_chunk=true \
  --expect-route-implemented search_file_chunks=true \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true \
  --output /tmp/querylake_db_compat_profile_smoke_aws_ready.json
python scripts/db_compat_profile_bringup_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-ready-projection-count 3 \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true \
  --output /tmp/querylake_db_compat_profile_bringup_aws_ready.json
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --expect-boot-ready false \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready false \
  --expect-declared-executable-routes-runtime-ready false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_bm25.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_file_chunks=projection_not_ready \
  --output /tmp/querylake_db_compat_profile_smoke_local.json
python scripts/db_compat_profile_bringup_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --expect-boot-ready false \
  --expect-configuration-ready true \
  --expect-route-runtime-ready false \
  --expect-declared-executable-routes-runtime-ready false \
  --expect-ready-projection-count 0 \
  --expect-projection-needing-build document_chunk_lexical_projection_v1 \
  --expect-route-runtime search_hybrid.document_chunk=false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready \
  --output /tmp/querylake_db_compat_profile_bringup_local.json
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-boot-ready true \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-route-implemented search_hybrid.document_chunk=true \
  --expect-route-implemented search_bm25.document_chunk=true \
  --expect-route-implemented search_file_chunks=true \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true \
  --output /tmp/querylake_db_compat_profile_smoke_local_ready.json
python scripts/db_compat_profile_bringup_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-ready-projection-count 3 \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true \
  --output /tmp/querylake_db_compat_profile_bringup_local_ready.json
python scripts/db_compat_local_profile_completion_gate.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-profile-implemented true \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-ready-projection-count 3 \
  --expect-declared-executable-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-degraded-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-gold-recommended-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --output /tmp/querylake_db_compat_local_profile_completion_gate.json
python scripts/db_compat_local_embedded_supported_slice_gate.py \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_embedded_supported_slice_gate.json
python scripts/db_compat_local_dense_sidecar_lifecycle_smoke.py \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_dense_sidecar_lifecycle_smoke.json
python scripts/db_compat_local_profile_consistency_check.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_profile_consistency.json
python scripts/db_compat_local_profile_promotion_status.py \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_profile_promotion_status.json
python scripts/db_compat_local_profile_scope_expansion_status.py \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_profile_scope_expansion_status.json
python scripts/db_compat_v2_runtime_consistency.py \
  --output /tmp/querylake_db_compat_v2_runtime_consistency.json
python scripts/db_compat_v2_program_completion_gate.py \
  --output /tmp/querylake_db_compat_v2_program_completion_gate.json
python scripts/db_compat_local_query_smoke.py \
  --enable-ready-profile-projections \
  --output /tmp/querylake_db_compat_local_profile_query_smoke.json
python scripts/db_compat_first_split_stack_completion_gate.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-backend-connectivity-ready true \
  --expect-required-projection-count 3 \
  --expect-ready-projection-count 3 \
  --expect-declared-executable-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-degraded-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-gold-recommended-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --output /tmp/querylake_db_compat_first_split_stack_completion_gate.json
python scripts/db_compat_program_completion_gate.py \
  --output /tmp/querylake_db_compat_program_completion_gate.json
python scripts/db_compat_retrieval_parity.py \
  --cases-json tests/fixtures/db_compat_retrieval_parity_cases.json \
  --route-thresholds-json tests/fixtures/db_compat_retrieval_parity_route_thresholds.json \
  --gold-runs-json tests/fixtures/db_compat_retrieval_parity_gold_runs.json \
  --split-runs-json tests/fixtures/db_compat_retrieval_parity_split_runs.json \
  --gold-latency-json tests/fixtures/db_compat_retrieval_parity_gold_latency.json \
  --split-latency-json tests/fixtures/db_compat_retrieval_parity_split_latency.json \
  --k 2 \
  --min-overlap 0.80 \
  --max-mrr-drop 0.10 \
  --max-latency-ratio 1.35 \
  --output /tmp/querylake_db_compat_retrieval_parity.json

pytest -q \
  tests/test_db_compat_profiles.py \
  tests/test_db_compat_api_router.py \
  tests/test_db_compat_retrieval_lanes.py \
  tests/test_db_compat_lane_executors.py \
  tests/test_db_compat_lexical_planner.py \
  tests/test_db_compat_search_surfaces.py \
  tests/test_db_compat_retrieval_explain.py \
  tests/test_db_compat_adapter_interfaces.py \
  tests/test_db_compat_projection_contracts.py \
  tests/test_db_compat_projection_registry.py \
  tests/test_db_compat_projection_writers.py \
  tests/test_db_compat_route_executors.py \
  tests/test_db_compat_opensearch_execution.py \
  tests/test_db_compat_projection_refresh.py \
  tests/test_db_compat_orchestrator_traces.py \
  tests/test_db_compat_contract_parity_harness.py \
  tests/test_db_compat_retrieval_parity_harness.py \
  tests/test_db_compat_profile_smoke_harness.py \
  tests/test_db_compat_profile_bringup.py \
  tests/test_db_compat_profile_bringup_smoke_harness.py \
  tests/test_db_compat_local_profile_doctor.py \
  tests/test_db_compat_local_dense_sidecar_sync.py \
  tests/test_db_compat_local_scope_expansion_sync.py \
  tests/test_db_compat_local_profile_sync.py \
  tests/test_db_compat_local_profile_completion_gate.py \
  tests/test_db_compat_local_embedded_supported_slice_gate.py \
  tests/test_db_compat_local_profile_consistency_check.py \
  tests/test_db_compat_local_profile_support_sync.py \
  tests/test_db_compat_local_query_smoke.py \
  tests/test_db_compat_local_dense_sidecar_lifecycle_smoke.py \
  tests/test_db_compat_local_profile_promotion_status.py \
  tests/test_db_compat_local_profile_scope_expansion_status.py \
  tests/test_db_compat_v2_runtime_consistency.py \
  tests/test_db_compat_v2_runtime_boundary_status.py \
  tests/test_db_compat_v2_runtime_boundary_sync.py \
  tests/test_db_compat_cross_surface_consistency.py \
  tests/test_db_compat_program_completion_gate.py \
  sdk/python/tests/test_client.py
