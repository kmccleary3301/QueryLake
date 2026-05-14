from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Literal, Optional

from QueryLake.scanning.contracts import GeometryLevel, SupportTier

BackendClass = Literal[
    "incumbent_continuity",
    "native_digital_extraction",
    "general_local_parser",
    "managed_general_parser",
    "premium_hard_document_escalator",
    "specialist_business_document",
    "scientific_stem",
    "cheap_offline_ocr",
    "experimental_local_doc_vlm",
]
DeploymentModel = Literal["local", "managed", "hybrid", "containerized", "external_service", "deferred"]
InvocationMode = Literal["sync_page", "sync_doc", "async_doc", "batch", "shadow", "deferred"]
RegistryStatus = Literal["active", "experimental", "disabled", "deferred", "watchlist", "deprecated"]
RoutingEligibility = Literal["default_eligible", "explicit_only", "shadow_only", "fallback_only", "deferred", "never"]


@dataclass(frozen=True)
class ScannerBackendSpec:
    backend_id: str
    display_name: str
    backend_class: BackendClass
    support_tier: SupportTier
    status: RegistryStatus
    owner: str
    promotion_state: str
    deprecation_policy: str
    input_types: List[str]
    document_class_fit: List[str]
    capture_mode_fit: List[str]
    language_profile: str
    structured_outputs_supported: List[str]
    geometry_level: GeometryLevel
    confidence_support: str
    native_text_support: bool
    ocr_support: bool
    specialty_tags: List[str]
    deployment_model: DeploymentModel
    invocation_mode: InvocationMode
    cost_class: str
    latency_class: str
    throughput_class: str
    privacy_class: str
    region_constraints: List[str]
    dependency_surface: List[str]
    routing_eligibility: RoutingEligibility
    hard_constraints: List[str] = field(default_factory=list)
    soft_preferences: List[str] = field(default_factory=list)
    fallback_role: Optional[str] = None
    escalation_only: bool = False
    budget_policy: Optional[str] = None
    latency_budget_policy: Optional[str] = None
    golden_doc_coverage: List[str] = field(default_factory=list)
    benchmark_status: str = "not_run"
    contract_test_suite: List[str] = field(default_factory=list)
    known_failure_modes: List[str] = field(default_factory=list)
    current_canary_status: Optional[str] = None
    rollback_target: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def validate_backend_spec(spec: ScannerBackendSpec) -> None:
    if not spec.backend_id or spec.backend_id.strip() != spec.backend_id:
        raise ValueError("backend_id must be non-empty and trimmed")
    if not spec.display_name:
        raise ValueError(f"{spec.backend_id}: display_name is required")
    if not spec.owner:
        raise ValueError(f"{spec.backend_id}: owner is required")
    if not spec.input_types:
        raise ValueError(f"{spec.backend_id}: input_types must not be empty")
    if not spec.document_class_fit:
        raise ValueError(f"{spec.backend_id}: document_class_fit must not be empty")
    if not spec.capture_mode_fit:
        raise ValueError(f"{spec.backend_id}: capture_mode_fit must not be empty")
    if spec.support_tier == "first_class" and not spec.contract_test_suite:
        raise ValueError(f"{spec.backend_id}: first_class backends require contract_test_suite metadata")
    if spec.support_tier == "premium_fallback":
        if not spec.escalation_only:
            raise ValueError(f"{spec.backend_id}: premium fallback backends must be escalation_only")
        if not spec.budget_policy:
            raise ValueError(f"{spec.backend_id}: premium fallback backends require budget_policy")
        if spec.routing_eligibility not in {"fallback_only", "explicit_only"}:
            raise ValueError(f"{spec.backend_id}: premium fallback must not be default eligible")
    if spec.support_tier in {"deferred", "watchlist", "low_ev"} and spec.routing_eligibility not in {"deferred", "never", "explicit_only"}:
        raise ValueError(f"{spec.backend_id}: deferred/watchlist/low_ev backends must not be default routed")
    if spec.routing_eligibility == "default_eligible" and spec.support_tier not in {"first_class", "experimental"}:
        raise ValueError(f"{spec.backend_id}: only first_class or experimental backends may be default eligible")


def validate_scanner_registry(registry: Dict[str, ScannerBackendSpec]) -> None:
    if not registry:
        raise ValueError("scanner registry must not be empty")
    for key, spec in registry.items():
        if key != spec.backend_id:
            raise ValueError(f"registry key '{key}' does not match backend_id '{spec.backend_id}'")
        validate_backend_spec(spec)


def get_backend_spec(registry: Dict[str, ScannerBackendSpec], backend_id: str) -> ScannerBackendSpec:
    try:
        return registry[backend_id]
    except KeyError as exc:
        raise KeyError(f"Unknown scanner backend_id: {backend_id}") from exc


def registry_report_rows(registry: Dict[str, ScannerBackendSpec]) -> List[Dict[str, Any]]:
    validate_scanner_registry(registry)
    rows: List[Dict[str, Any]] = []
    for backend_id in sorted(registry):
        spec = registry[backend_id]
        rows.append(
            {
                "backend_id": spec.backend_id,
                "display_name": spec.display_name,
                "backend_class": spec.backend_class,
                "support_tier": spec.support_tier,
                "status": spec.status,
                "routing_eligibility": spec.routing_eligibility,
                "deployment_model": spec.deployment_model,
                "geometry_level": spec.geometry_level,
                "cost_class": spec.cost_class,
                "privacy_class": spec.privacy_class,
                "benchmark_status": spec.benchmark_status,
            }
        )
    return rows


def _spec(**kwargs: Any) -> ScannerBackendSpec:
    spec = ScannerBackendSpec(**kwargs)
    validate_backend_spec(spec)
    return spec


def build_default_scanner_registry() -> Dict[str, ScannerBackendSpec]:
    registry = {
        "chandra_1": _spec(
            backend_id="chandra_1",
            display_name="Chandra 1 OCR",
            backend_class="incumbent_continuity",
            support_tier="first_class",
            status="active",
            owner="scanner",
            promotion_state="continuity_default",
            deprecation_policy="replace only after no-regression evidence and rollback plan",
            input_types=["application/pdf", "image/png", "image/jpeg"],
            document_class_fit=["scanned_pdf", "mixed_pdf", "image_document"],
            capture_mode_fit=["scanned", "mixed", "photo"],
            language_profile="general",
            structured_outputs_supported=["markdown", "page_metadata"],
            geometry_level="page",
            confidence_support="not_exposed",
            native_text_support=False,
            ocr_support=True,
            specialty_tags=["continuity", "ocr_markdown"],
            deployment_model="hybrid",
            invocation_mode="sync_page",
            cost_class="local_runtime",
            latency_class="medium",
            throughput_class="batchable_pages",
            privacy_class="local_or_private_external_vllm",
            region_constraints=[],
            dependency_surface=["ray", "pypdfium2", "pillow", "chandra_runtime"],
            routing_eligibility="default_eligible",
            hard_constraints=["requires chandra handle"],
            soft_preferences=["use for current OCR compatibility"],
            fallback_role="current_ocr_default",
            escalation_only=False,
            budget_policy="local_runtime_budget",
            latency_budget_policy="profile_concurrency_budget",
            golden_doc_coverage=["scanned_pdf", "mixed_pdf"],
            benchmark_status="existing_chandra_suite",
            contract_test_suite=["scanner_contract_chandra_compat_v1"],
            known_failure_modes=["runtime unavailable", "render dependency unavailable"],
            current_canary_status="continuity",
            rollback_target=None,
        ),
        "chandra_2": _spec(
            backend_id="chandra_2",
            display_name="Chandra 2 OCR",
            backend_class="incumbent_continuity",
            support_tier="experimental",
            status="experimental",
            owner="scanner",
            promotion_state="experimental_only",
            deprecation_policy="can be disabled without affecting stable ingestion",
            input_types=["application/pdf", "image/png", "image/jpeg"],
            document_class_fit=["scanned_pdf", "mixed_pdf", "image_document"],
            capture_mode_fit=["scanned", "mixed", "photo"],
            language_profile="general",
            structured_outputs_supported=["markdown", "page_metadata"],
            geometry_level="page",
            confidence_support="not_exposed",
            native_text_support=False,
            ocr_support=True,
            specialty_tags=["experimental", "ocr_markdown"],
            deployment_model="hybrid",
            invocation_mode="sync_page",
            cost_class="local_runtime",
            latency_class="medium",
            throughput_class="batchable_pages",
            privacy_class="local_or_private_external_vllm",
            region_constraints=[],
            dependency_surface=["ray", "pypdfium2", "pillow", "chandra_runtime"],
            routing_eligibility="explicit_only",
            hard_constraints=["requires chandra2 handle"],
            soft_preferences=["benchmark only"],
            fallback_role=None,
            escalation_only=False,
            budget_policy="local_runtime_budget",
            latency_budget_policy="profile_concurrency_budget",
            golden_doc_coverage=["scanned_pdf"],
            benchmark_status="experimental_chandra_suite",
            contract_test_suite=["scanner_contract_chandra_compat_v1"],
            known_failure_modes=["experimental model drift"],
            current_canary_status="experimental",
            rollback_target="chandra_1",
        ),
        "pymupdf4llm_native": _spec(
            backend_id="pymupdf4llm_native",
            display_name="PyMuPDF4LLM Native Extraction",
            backend_class="native_digital_extraction",
            support_tier="first_class",
            status="active",
            owner="scanner",
            promotion_state="candidate",
            deprecation_policy="replace only if native extraction quality and contract coverage improve",
            input_types=["application/pdf"],
            document_class_fit=["born_digital_pdf", "report", "paper"],
            capture_mode_fit=["born_digital"],
            language_profile="pdf_text_layer_general",
            structured_outputs_supported=["markdown", "json", "text"],
            geometry_level="block",
            confidence_support="not_exposed",
            native_text_support=True,
            ocr_support=False,
            specialty_tags=["native_text", "rag_markdown"],
            deployment_model="local",
            invocation_mode="sync_doc",
            cost_class="local_cpu",
            latency_class="low",
            throughput_class="document_sync",
            privacy_class="local",
            region_constraints=[],
            dependency_surface=["pymupdf4llm", "pymupdf"],
            routing_eligibility="default_eligible",
            hard_constraints=["requires pymupdf4llm dependency"],
            soft_preferences=["prefer for born-digital PDFs when quality gates pass"],
            fallback_role="native_first",
            escalation_only=False,
            budget_policy="local_cpu_budget",
            latency_budget_policy="native_extract_budget",
            golden_doc_coverage=["born_digital_pdf"],
            benchmark_status="not_run",
            contract_test_suite=["scanner_contract_native_text_v1"],
            known_failure_modes=["malformed PDF text layer", "weak reading order"],
            current_canary_status="not_started",
            rollback_target="chandra_1",
        ),
        "docling_local": _spec(
            backend_id="docling_local",
            display_name="Docling Local Parser",
            backend_class="general_local_parser",
            support_tier="first_class",
            status="active",
            owner="scanner",
            promotion_state="candidate",
            deprecation_policy="replace only after local parser eval evidence",
            input_types=["application/pdf", "image/png", "image/jpeg", "text/html"],
            document_class_fit=["scanned_pdf", "mixed_pdf", "tables_heavy", "reports", "papers"],
            capture_mode_fit=["born_digital", "scanned", "mixed", "photo"],
            language_profile="general_multiformat",
            structured_outputs_supported=["markdown", "json", "layout", "tables", "figures"],
            geometry_level="table_cell",
            confidence_support="partial_or_backend_specific",
            native_text_support=True,
            ocr_support=True,
            specialty_tags=["local_parser", "layout", "tables"],
            deployment_model="local",
            invocation_mode="sync_doc",
            cost_class="local_cpu_or_gpu",
            latency_class="medium",
            throughput_class="document_sync",
            privacy_class="local",
            region_constraints=[],
            dependency_surface=["docling"],
            routing_eligibility="explicit_only",
            hard_constraints=["requires docling dependency"],
            soft_preferences=["primary local parser candidate after contract gates"],
            fallback_role="local_parser_primary",
            escalation_only=False,
            budget_policy="local_runtime_budget",
            latency_budget_policy="local_parser_budget",
            golden_doc_coverage=["scanned_pdf", "tables_heavy", "mixed_pdf"],
            benchmark_status="not_run",
            contract_test_suite=["scanner_contract_docling_v1"],
            known_failure_modes=["dependency footprint", "table cell drift", "OCR option variance"],
            current_canary_status="not_started",
            rollback_target="chandra_1",
        ),
        "mineru_shadow": _spec(
            backend_id="mineru_shadow",
            display_name="MinerU Shadow Parser",
            backend_class="general_local_parser",
            support_tier="shadow",
            status="experimental",
            owner="scanner",
            promotion_state="shadow_only",
            deprecation_policy="disable if dependency or output contract is unstable",
            input_types=["application/pdf", "image/png", "image/jpeg"],
            document_class_fit=["scanned_pdf", "mixed_pdf", "tables_heavy", "papers"],
            capture_mode_fit=["born_digital", "scanned", "mixed", "photo"],
            language_profile="general_multiformat",
            structured_outputs_supported=["markdown", "json", "layout"],
            geometry_level="block",
            confidence_support="backend_specific",
            native_text_support=True,
            ocr_support=True,
            specialty_tags=["shadow", "local_parser", "benchmark_canary"],
            deployment_model="local",
            invocation_mode="shadow",
            cost_class="local_cpu_or_gpu",
            latency_class="medium_high",
            throughput_class="document_sync",
            privacy_class="local",
            region_constraints=[],
            dependency_surface=["mineru"],
            routing_eligibility="shadow_only",
            hard_constraints=["requires mineru dependency"],
            soft_preferences=["compare against Docling and Chandra"],
            fallback_role=None,
            escalation_only=False,
            budget_policy="shadow_eval_budget",
            latency_budget_policy="shadow_eval_budget",
            golden_doc_coverage=["scanned_pdf", "tables_heavy"],
            benchmark_status="not_run",
            contract_test_suite=["scanner_contract_shadow_v1"],
            known_failure_modes=["dependency footprint", "contract instability"],
            current_canary_status="not_started",
            rollback_target=None,
        ),
        "mistral_ocr": _spec(
            backend_id="mistral_ocr",
            display_name="Mistral OCR / Document AI",
            backend_class="managed_general_parser",
            support_tier="first_class",
            status="active",
            owner="scanner",
            promotion_state="candidate",
            deprecation_policy="disable or pin if provider version drift breaks contracts",
            input_types=["application/pdf", "image/png", "image/jpeg"],
            document_class_fit=["scanned_pdf", "mixed_pdf", "tables_heavy", "reports"],
            capture_mode_fit=["scanned", "mixed", "photo", "born_digital"],
            language_profile="managed_general",
            structured_outputs_supported=["markdown", "images", "bbox", "annotations"],
            geometry_level="polygon",
            confidence_support="provider_specific",
            native_text_support=True,
            ocr_support=True,
            specialty_tags=["managed", "markdown", "ocr"],
            deployment_model="managed",
            invocation_mode="async_doc",
            cost_class="managed_per_page",
            latency_class="medium",
            throughput_class="provider_batchable",
            privacy_class="managed_policy_required",
            region_constraints=["provider_region_policy"],
            dependency_surface=["mistral_api"],
            routing_eligibility="fallback_only",
            hard_constraints=["requires credentials", "requires managed policy allow"],
            soft_preferences=["fallback after local parser failure or explicit managed route"],
            fallback_role="managed_parser_fallback",
            escalation_only=False,
            budget_policy="managed_parser_budget",
            latency_budget_policy="managed_parser_budget",
            golden_doc_coverage=["scanned_pdf", "tables_heavy", "mixed_pdf"],
            benchmark_status="not_run",
            contract_test_suite=["scanner_contract_mistral_ocr_v1"],
            known_failure_modes=["provider outage", "rate limit", "version drift", "credential unavailable"],
            current_canary_status="not_started",
            rollback_target="docling_local",
        ),
        "gemini_document_fallback": _spec(
            backend_id="gemini_document_fallback",
            display_name="Gemini Document Premium Fallback",
            backend_class="premium_hard_document_escalator",
            support_tier="premium_fallback",
            status="active",
            owner="scanner",
            promotion_state="candidate",
            deprecation_policy="disable if preview/provider drift breaks contracts or cost budget",
            input_types=["application/pdf", "image/png", "image/jpeg"],
            document_class_fit=["hard_visual_document", "photo", "screenshot", "charts", "figures"],
            capture_mode_fit=["photo", "screenshot", "vision_only", "mixed"],
            language_profile="premium_multimodal",
            structured_outputs_supported=["text", "markdown", "structured_json"],
            geometry_level="page",
            confidence_support="not_exposed_or_provider_specific",
            native_text_support=True,
            ocr_support=True,
            specialty_tags=["premium", "fallback", "hard_document", "vision"],
            deployment_model="managed",
            invocation_mode="async_doc",
            cost_class="premium_token_or_page",
            latency_class="high",
            throughput_class="provider_limited",
            privacy_class="premium_managed_policy_required",
            region_constraints=["provider_region_policy"],
            dependency_surface=["gemini_api"],
            routing_eligibility="fallback_only",
            hard_constraints=["requires credentials", "requires premium policy allow", "requires budget allow"],
            soft_preferences=["hard-page escalation only"],
            fallback_role="premium_escalator",
            escalation_only=True,
            budget_policy="premium_escalation_budget_explicit_opt_in",
            latency_budget_policy="premium_escalation_budget",
            golden_doc_coverage=["photo", "screenshot", "charts"],
            benchmark_status="not_run",
            contract_test_suite=["scanner_contract_premium_fallback_v1"],
            known_failure_modes=["provider outage", "preview drift", "cost spike", "prompt sensitivity"],
            current_canary_status="not_started",
            rollback_target="mistral_ocr",
        ),
    }
    validate_scanner_registry(registry)
    return registry


def filter_registry_by_support_tier(
    registry: Dict[str, ScannerBackendSpec],
    tiers: Iterable[SupportTier],
) -> Dict[str, ScannerBackendSpec]:
    tier_set = set(tiers)
    return {backend_id: spec for backend_id, spec in registry.items() if spec.support_tier in tier_set}
