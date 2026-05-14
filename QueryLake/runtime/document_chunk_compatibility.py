from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class DocumentChunkRetirementReadiness:
    ready: bool
    blockers: list[str]
    checks: Dict[str, bool]

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_document_chunk_retirement_readiness(
    *,
    public_segment_retrieval_stable: bool = False,
    sdk_ui_segment_response_support: bool = False,
    historical_tail_resolved_or_isolated: bool = False,
    backend_segment_route_coverage: bool = False,
    migration_guide_exists: bool = False,
) -> DocumentChunkRetirementReadiness:
    checks = {
        "public_segment_retrieval_stable": bool(public_segment_retrieval_stable),
        "sdk_ui_segment_response_support": bool(sdk_ui_segment_response_support),
        "historical_tail_resolved_or_isolated": bool(historical_tail_resolved_or_isolated),
        "backend_segment_route_coverage": bool(backend_segment_route_coverage),
        "migration_guide_exists": bool(migration_guide_exists),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return DocumentChunkRetirementReadiness(ready=len(blockers) == 0, blockers=blockers, checks=checks)
