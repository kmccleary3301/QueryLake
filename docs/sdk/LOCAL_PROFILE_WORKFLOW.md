# Local Profile SDK Workflow

This is the minimal SDK workflow for the supported embedded slice.

## 1. Inspect capabilities

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://localhost:8000")

capabilities = client.capabilities_summary()
print(capabilities.profile.id)
print(client.representation_scopes())
print(client.route_support_manifest_v2())
```

## 2. Inspect bring-up

```python
bringup = client.profile_bringup_summary()

print(bringup.summary.route_runtime_ready)
print(bringup.summary.declared_executable_routes_runtime_ready)
print(bringup.local_dense_sidecar_contract())
print(bringup.local_dense_sidecar_cache_lifecycle_state())
print(bringup.local_scope_expansion_status())
```

## 3. Inspect route support

```python
print(client.route_representation_scope_id_from_capabilities("search_hybrid.document_chunk"))
print(client.route_capability_dependencies_from_capabilities("search_hybrid.document_chunk"))
print(client.bringup_route_recovery_entry("search_hybrid.document_chunk"))
```

## 4. Inspect widening status

```python
print(client.local_scope_expansion_contract())
print(client.local_scope_expansion_required_before_widening())
print(client.local_scope_expansion_future_scope_candidates())
```

## 5. Operate safely

The supported embedded slice is intentionally narrow.

Use it for:

- local lexical retrieval
- local lexical+dense hybrid
- file lexical retrieval

Do not assume support for:

- sparse retrieval
- exact hard lexical constraints
- widened local route families beyond the frozen supported slice
