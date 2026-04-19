from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class LexicalVariantSpec(BaseModel):
    variant_id: str
    description: str
    enable_sequence_expansion: bool = True
    max_bigram_windows: Optional[int] = None
    max_trigram_windows: Optional[int] = None
    catch_all_field_weights: Dict[str, float] = Field(default_factory=lambda: {"text": 1.0})
    exactness_mode: str = "off"  # off | title_id | title_id_phrase
    proximity_mode: str = "off"  # off | current | constrained | sdm_lite_proxy
    priors_mode: str = "off"
    rescore_window: Optional[int] = None
    apply_query_classes: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    def to_payload(self) -> Dict[str, object]:
        return self.model_dump()


_REGISTRY: Dict[str, LexicalVariantSpec] = {
    "QL-L0": LexicalVariantSpec(
        variant_id="QL-L0",
        description="Plain BM25 control with sequence-window expansion disabled.",
        enable_sequence_expansion=False,
        proximity_mode="off",
        notes=["control", "plain_bm25"],
    ),
    "QL-L1": LexicalVariantSpec(
        variant_id="QL-L1",
        description="Current heuristic control with universal contiguous 2/3-term phrase-window expansion.",
        enable_sequence_expansion=True,
        proximity_mode="current",
        catch_all_field_weights={"text": 1.0},
        notes=["control", "current_heuristic"],
    ),
    "QL-L3": LexicalVariantSpec(
        variant_id="QL-L3",
        description="Field-aware lexical baseline using weighted multi-field catch-all compilation.",
        enable_sequence_expansion=False,
        proximity_mode="off",
        catch_all_field_weights={"text": 1.0, "document_name": 3.0, "website_url": 1.5},
        notes=["core", "field_aware"],
    ),
    "QL-L4": LexicalVariantSpec(
        variant_id="QL-L4",
        description="Field-aware lexical baseline plus exact title/name/id features.",
        enable_sequence_expansion=False,
        exactness_mode="title_id",
        proximity_mode="off",
        catch_all_field_weights={"text": 1.0, "document_name": 3.0, "website_url": 1.5},
        notes=["core", "field_aware", "exactness"],
    ),
    "QL-L5": LexicalVariantSpec(
        variant_id="QL-L5",
        description="Field-aware + exactness + constrained phrase/proximity gated by query class and query length.",
        enable_sequence_expansion=True,
        exactness_mode="title_id",
        proximity_mode="constrained",
        max_bigram_windows=8,
        max_trigram_windows=6,
        catch_all_field_weights={"text": 1.0, "document_name": 3.0, "website_url": 1.5},
        apply_query_classes=["phrase_sensitive", "navigational_exact", "short_keyword"],
        notes=["core", "field_aware", "exactness", "constrained_proximity"],
    ),
    "QL-L6": LexicalVariantSpec(
        variant_id="QL-L6",
        description="Field-aware + exactness with simple priors benchmark.",
        enable_sequence_expansion=False,
        exactness_mode="title_id",
        priors_mode="simple_static",
        catch_all_field_weights={"text": 1.0, "document_name": 3.0, "website_url": 1.5},
        notes=["secondary", "priors"],
    ),
    "QL-L9": LexicalVariantSpec(
        variant_id="QL-L9",
        description="Bounded lexical top-N rescoring candidate.",
        enable_sequence_expansion=False,
        exactness_mode="title_id",
        proximity_mode="off",
        catch_all_field_weights={"text": 1.0, "document_name": 3.0, "website_url": 1.5},
        rescore_window=100,
        notes=["secondary", "rescore"],
    ),
}


DEFAULT_LEXICAL_VARIANT_ID = "QL-L1"


def list_lexical_variant_specs() -> List[LexicalVariantSpec]:
    return [spec.model_copy(deep=True) for spec in _REGISTRY.values()]


def get_lexical_variant_spec(variant_id: Optional[str]) -> LexicalVariantSpec:
    resolved = str(variant_id or DEFAULT_LEXICAL_VARIANT_ID).strip() or DEFAULT_LEXICAL_VARIANT_ID
    if resolved not in _REGISTRY:
        valid = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Unknown lexical variant '{resolved}'. Valid variants: {valid}")
    return _REGISTRY[resolved].model_copy(deep=True)
