from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from QueryLake.misc_functions.paradedb_query_parser import (
    CompiledSearchQuery,
    ParsedSearchState,
    build_search_debug_payload,
    compile_search_state,
    normalize_search_input,
    parse_search_state,
)
from QueryLake.runtime.lexical_variant_registry import LexicalVariantSpec, get_lexical_variant_spec

_IDENTIFIER_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:/#-]{6,}$")
_HASHISH_RE = re.compile(r"^[0-9a-f]{8,}$", re.IGNORECASE)
_QUESTION_WORD_RE = re.compile(r"\b(how|what|why|when|where|which|should|can|could|prevent|reduce)\b", re.IGNORECASE)


@dataclass(frozen=True)
class LexicalQueryPlan:
    variant_id: str
    variant_description: str
    query_class: str
    state: ParsedSearchState
    compiled: CompiledSearchQuery
    formatted_query: str
    strong_where_clause: Optional[str]
    catch_all_fields: List[str]
    catch_all_field_weights: Dict[str, float]
    exactness_clauses: List[str] = field(default_factory=list)
    debug: Dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "variant_description": self.variant_description,
            "query_class": self.query_class,
            "catch_all_fields": list(self.catch_all_fields),
            "catch_all_field_weights": dict(self.catch_all_field_weights),
            "exactness_clauses": list(self.exactness_clauses),
            "formatted_query": self.formatted_query,
            "strong_where_clause": self.strong_where_clause,
            "debug": dict(self.debug),
        }


def classify_lexical_query(raw_query_text: str, state: Optional[ParsedSearchState] = None) -> str:
    normalized = normalize_search_input(str(raw_query_text or "")).strip()
    if not normalized:
        return "empty"
    tokens = [token for token in normalized.replace('"', " ").split() if token]
    token_count = len(tokens)
    lowered = normalized.lower()

    if state is not None and (len(state.necessary_args) > 0 or len(state.args_parsed_negative) > 0):
        return "operator_constrained"
    if any(_HASHISH_RE.match(token) for token in tokens):
        return "identifier_exact"
    if any(_IDENTIFIER_TOKEN_RE.match(token) for token in tokens) and token_count <= 4:
        return "identifier_exact"
    if normalized.startswith('"') and normalized.endswith('"') and token_count <= 6:
        return "navigational_exact"
    if token_count <= 3:
        return "short_keyword"
    if token_count >= 8 or bool(_QUESTION_WORD_RE.search(lowered)):
        return "exploratory_natural_language"
    return "phrase_sensitive"


def _default_catch_all_fields(
    requested: Sequence[str],
    valid_fields: Sequence[str],
    weights: Dict[str, float],
) -> List[str]:
    effective: List[str] = []
    seen = set()
    for field in list(requested or []):
        if field in valid_fields and field not in seen:
            effective.append(str(field))
            seen.add(str(field))
    for field in weights:
        if field in valid_fields and field not in seen:
            effective.append(str(field))
            seen.add(str(field))
    return effective or [str(requested[0] if requested else "text")]


def _should_enable_constrained_proximity(
    variant: LexicalVariantSpec,
    *,
    query_class: str,
    raw_query_text: str,
) -> bool:
    if variant.proximity_mode != "constrained":
        return bool(variant.enable_sequence_expansion)
    if variant.apply_query_classes and query_class not in set(variant.apply_query_classes):
        return False
    token_count = len([token for token in normalize_search_input(raw_query_text).split() if token])
    return token_count <= 8


def _sanitize_exact_phrase_text(raw_query_text: str) -> str:
    normalized = normalize_search_input(raw_query_text).strip().strip('"').strip("'")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace('"', " ")
    return normalized.strip()


def _build_exactness_clauses(
    *,
    raw_query_text: str,
    query_class: str,
    valid_fields: Sequence[str],
    exactness_mode: str,
) -> List[str]:
    if exactness_mode == "off":
        return []
    exact_phrase = _sanitize_exact_phrase_text(raw_query_text)
    if not exact_phrase:
        return []
    phrase_term = f"\"{exact_phrase}\""
    clauses: List[str] = []
    if "document_name" in valid_fields and query_class in {"identifier_exact", "navigational_exact", "short_keyword", "phrase_sensitive"}:
        clauses.append(f"(document_name:{phrase_term})^12")
    if "file_name" in valid_fields and query_class in {"identifier_exact", "navigational_exact", "short_keyword"}:
        clauses.append(f"(file_name:{phrase_term})^14")
    if "integrity_sha256" in valid_fields and query_class == "identifier_exact":
        clauses.append(f"(integrity_sha256:{phrase_term})^20")
    if "website_url" in valid_fields and query_class in {"identifier_exact", "navigational_exact"}:
        clauses.append(f"(website_url:{phrase_term})^6")
    return clauses


def build_paradedb_lexical_query_plan(
    raw_query_text: str,
    *,
    valid_fields: Sequence[str],
    catch_all_fields: Sequence[str],
    variant_id: Optional[str] = None,
) -> LexicalQueryPlan:
    variant = get_lexical_variant_spec(variant_id)
    initial_state = parse_search_state(
        raw_query_text,
        valid_fields,
        enable_sequence_expansion=False,
    )
    query_class = classify_lexical_query(raw_query_text, initial_state)
    enable_sequence_expansion = _should_enable_constrained_proximity(
        variant,
        query_class=query_class,
        raw_query_text=raw_query_text,
    )
    effective_fields = _default_catch_all_fields(catch_all_fields, valid_fields, variant.catch_all_field_weights)
    state = parse_search_state(
        raw_query_text,
        valid_fields,
        enable_sequence_expansion=enable_sequence_expansion,
        max_bigram_windows=variant.max_bigram_windows,
        max_trigram_windows=variant.max_trigram_windows,
    )
    compiled = compile_search_state(
        state,
        catch_all_fields=effective_fields,
        catch_all_field_weights=variant.catch_all_field_weights,
    )
    exactness_clauses = _build_exactness_clauses(
        raw_query_text=raw_query_text,
        query_class=query_class,
        valid_fields=valid_fields,
        exactness_mode=variant.exactness_mode,
    )
    formatted_query = compiled.final_query
    if exactness_clauses:
        exactness_block = " OR ".join(exactness_clauses)
        formatted_query = (
            f"({formatted_query}) OR ({exactness_block})"
            if formatted_query not in {"()", ""}
            else f"({exactness_block})"
        )
    debug = build_search_debug_payload(
        state,
        compiled,
        catch_all_fields=effective_fields,
        catch_all_field_weights=variant.catch_all_field_weights,
    )
    debug.update(
        {
            "variant_id": variant.variant_id,
            "query_class": query_class,
            "exactness_mode": variant.exactness_mode,
            "proximity_mode": variant.proximity_mode,
            "priors_mode": variant.priors_mode,
            "exactness_clause_count": len(exactness_clauses),
        }
    )
    return LexicalQueryPlan(
        variant_id=variant.variant_id,
        variant_description=variant.description,
        query_class=query_class,
        state=state,
        compiled=compiled,
        formatted_query=formatted_query,
        strong_where_clause=compiled.strong_where_clause,
        catch_all_fields=effective_fields,
        catch_all_field_weights=dict(variant.catch_all_field_weights),
        exactness_clauses=exactness_clauses,
        debug=debug,
    )
