from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from ..database.sql_db_tables import CHUNK_INDEXED_COLUMNS

VALID_FIELDS = CHUNK_INDEXED_COLUMNS

_QUOTE_SEGMENT_RE = re.compile(r"\"([^\"]*)\"(\~\d+)?(\^\d+(\.\d+)?)?")
_QUOTE_CLEAN_RE = re.compile(r"(\'|\")")
_FIELD_RE = re.compile(r"^([a-zA-Z0-9_.]+)\:")
_BOOST_RE = re.compile(r"\^(\d+(\.\d+)?)$")
_SLOP_RE = re.compile(r"\~(\d+)$")
_FORBIDDEN_CHARS = "\\+^`:{}[]()~!*',|&<>?/=;$"
_SANITIZE_TABLE = str.maketrans("", "", _FORBIDDEN_CHARS)


def field_match_format(field: str, value: str) -> str:
    return f"{field}:{value}"


def _append_unique(values: List[str], seen: set, candidate: str) -> None:
    if candidate in seen:
        return
    seen.add(candidate)
    values.append(candidate)


def _format_boost(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def _weighted_clause(field: str, value: str, weight: float) -> str:
    clause = field_match_format(field, value)
    if abs(float(weight) - 1.0) <= 1e-9:
        return clause
    return f"({clause})^{_format_boost(float(weight))}"


def normalize_search_input(text_in: str) -> str:
    assert isinstance(text_in, str), "Search text must be a string"
    text_in = text_in[:4000]
    text_in = "".join(ch if ch.isprintable() else " " for ch in text_in)
    return text_in.replace("AND", "and").replace("OR", "or").replace("NOT", "not").replace("\n", " ")


@dataclass(frozen=True)
class ParsedSearchState:
    raw_query_text: str
    normalized_query_text: str
    valid_fields: Tuple[str, ...]
    necessary_args: Tuple[Tuple[str, str], ...]
    args_parsed: Tuple[Tuple[str, Optional[str]], ...]
    args_parsed_negative: Tuple[Tuple[str, Optional[str]], ...]
    term_sequences: Tuple[Tuple[str, ...], ...]
    two_term_sequences: Tuple[str, ...]
    three_term_sequences: Tuple[str, ...]
    phrase_arguments: Dict[str, str]
    id_exclusions: Tuple[str, ...]
    enable_sequence_expansion: bool
    max_bigram_windows: Optional[int]
    max_trigram_windows: Optional[int]
    two_sequence_slop: int
    three_sequence_slop: int
    two_sequence_boost: float
    three_sequence_boost: float
    quoted_phrase_default_boost: float


@dataclass(frozen=True)
class CompiledSearchQuery:
    final_query: str
    strong_where_clause: Optional[str]
    positive_clauses: Tuple[str, ...]
    negative_clauses: Tuple[str, ...]
    necessary_clauses: Tuple[str, ...]
    total_clause_count: int


def parse_search_state(
    text_in: str,
    valid_fields: Sequence[str],
    *,
    enable_sequence_expansion: bool = True,
    max_bigram_windows: Optional[int] = None,
    max_trigram_windows: Optional[int] = None,
    two_sequence_slop: int = 2,
    three_sequence_slop: int = 3,
    two_sequence_boost: float = 20.0,
    three_sequence_boost: float = 60.0,
    quoted_phrase_default_boost: float = 40.0,
) -> ParsedSearchState:
    normalized_query = normalize_search_input(text_in)

    id_exclusions: List[str] = []
    call = normalized_query
    phrase_arguments: Dict[str, str] = {}
    quote_segments = _QUOTE_SEGMENT_RE.finditer(call)

    for i, segment in enumerate(list(quote_segments)):
        phrase_arguments[f"quote_arg_{i}"] = segment.group(0)

    for key, value in phrase_arguments.items():
        call = call.replace(key, f"%{key}")
        call = call.replace(value, key)

    call = _QUOTE_CLEAN_RE.sub(" ", call)
    terms = call.split(" ")

    necessary_args: List[Tuple[str, str]] = []
    args_parsed: List[Tuple[str, Optional[str]]] = []
    args_parsed_negative: List[Tuple[str, Optional[str]]] = []
    term_sequences: List[List[str]] = []
    current_term_sequence: List[str] = []

    for term in terms:
        term_is_quote_arg = False
        slop = 1
        boost = 1.0
        field = None

        negative = term.startswith("-")
        term = term.strip("-")

        field_specified = _FIELD_RE.search(term)
        if field_specified:
            field = field_specified.group(1)
            term = term[len(field) + 1 :]

        if not (field in valid_fields or (isinstance(field, str) and field.split(".")[0] in valid_fields)):
            field = None

        if term in phrase_arguments:
            term_is_quote_arg = True
            term = phrase_arguments[term]

        boost_specified = _BOOST_RE.search(term)
        if boost_specified:
            boost = float(boost_specified.group(1))
            term = term[: boost_specified.start()]
        elif term_is_quote_arg and not negative:
            boost = float(quoted_phrase_default_boost)

        slop_specified = _SLOP_RE.search(term)
        if slop_specified:
            slop = int(slop_specified.group(1))
            term = term[: slop_specified.start()]

        term = term.translate(_SANITIZE_TABLE)

        if term_is_quote_arg:
            term = term.strip("\"")
            term = term.replace("\"", " ")
            term = f"\"{term.strip()}\""

        if term.strip() in {"", "\"\""}:
            continue

        if slop != 1 and term_is_quote_arg and not negative:
            term = f"{term}~{slop}"

        if boost != 1 and not negative:
            term = f"{term}^{_format_boost(boost)}"

        if (not negative) and (not term_is_quote_arg) and (field is None):
            current_term_sequence.append(term)
        else:
            if current_term_sequence:
                term_sequences.append(current_term_sequence)
            current_term_sequence = []

        if negative:
            args_parsed_negative.append((term, field))
        elif field is not None:
            necessary_args.append((term, field))
        else:
            args_parsed.append((term, field))

    if current_term_sequence:
        term_sequences.append(current_term_sequence)

    two_term_sequences: List[str] = []
    three_term_sequences: List[str] = []
    for term_sequence in term_sequences:
        if len(term_sequence) > 1:
            for i in range(1, len(term_sequence)):
                two_term_sequences.append(f"{term_sequence[i - 1]} {term_sequence[i]}")
        if len(term_sequence) > 2:
            for i in range(2, len(term_sequence)):
                three_term_sequences.append(f"{term_sequence[i - 2]} {term_sequence[i - 1]} {term_sequence[i]}")

    if enable_sequence_expansion:
        if max_bigram_windows is not None:
            two_term_sequences = two_term_sequences[: int(max_bigram_windows)]
        if max_trigram_windows is not None:
            three_term_sequences = three_term_sequences[: int(max_trigram_windows)]

        for entry in two_term_sequences:
            args_parsed.append((f"\"{entry}\"~{int(two_sequence_slop)}^{_format_boost(float(two_sequence_boost))}", None))
        for entry in three_term_sequences:
            args_parsed.append((f"\"{entry}\"~{int(three_sequence_slop)}^{_format_boost(float(three_sequence_boost))}", None))
    else:
        two_term_sequences = []
        three_term_sequences = []

    return ParsedSearchState(
        raw_query_text=str(text_in),
        normalized_query_text=normalized_query,
        valid_fields=tuple(str(v) for v in valid_fields),
        necessary_args=tuple((str(term), str(field)) for term, field in necessary_args),
        args_parsed=tuple((str(term), field if field is None else str(field)) for term, field in args_parsed),
        args_parsed_negative=tuple((str(term), field if field is None else str(field)) for term, field in args_parsed_negative),
        term_sequences=tuple(tuple(seq) for seq in term_sequences),
        two_term_sequences=tuple(two_term_sequences),
        three_term_sequences=tuple(three_term_sequences),
        phrase_arguments=dict(phrase_arguments),
        id_exclusions=tuple(id_exclusions),
        enable_sequence_expansion=bool(enable_sequence_expansion),
        max_bigram_windows=max_bigram_windows,
        max_trigram_windows=max_trigram_windows,
        two_sequence_slop=int(two_sequence_slop),
        three_sequence_slop=int(three_sequence_slop),
        two_sequence_boost=float(two_sequence_boost),
        three_sequence_boost=float(three_sequence_boost),
        quoted_phrase_default_boost=float(quoted_phrase_default_boost),
    )


def compile_search_state(
    state: ParsedSearchState,
    *,
    catch_all_fields: Sequence[str] = ("text",),
    catch_all_field_weights: Optional[Dict[str, float]] = None,
) -> CompiledSearchQuery:
    catch_all_weights = {
        str(field): float(weight)
        for field, weight in dict(catch_all_field_weights or {}).items()
    }
    for field in catch_all_fields:
        assert field in state.valid_fields, (
            f"Invalid field '{field}' in catch_all_fields. Valid fields are: {state.valid_fields}"
        )

    p_fields: List[str] = []
    n_fields: List[str] = []
    p_seen = set()
    n_seen = set()

    for entry, field in state.args_parsed:
        if field is None:
            for catch_all_field in catch_all_fields:
                _append_unique(
                    p_fields,
                    p_seen,
                    _weighted_clause(
                        str(catch_all_field),
                        str(entry),
                        catch_all_weights.get(str(catch_all_field), 1.0),
                    ),
                )
        else:
            _append_unique(p_fields, p_seen, field_match_format(str(field), str(entry)))

    for entry, field in state.args_parsed_negative:
        if field is None:
            for catch_all_field in catch_all_fields:
                _append_unique(n_fields, n_seen, field_match_format(str(catch_all_field), str(entry)))
        else:
            _append_unique(n_fields, n_seen, field_match_format(str(field), str(entry)))

    negative_field = " NOT ".join(n_fields)
    positive_field = " OR ".join(p_fields)
    single_condition = f"({positive_field}) NOT {negative_field}" if n_fields else f"({positive_field})"

    necessary_unique = list(dict.fromkeys([field_match_format(field, term) for term, field in state.necessary_args]))
    if necessary_unique:
        necessary_joined = " AND ".join(necessary_unique)
        final_query = (
            f"{necessary_joined} AND {single_condition}"
            if (len(state.args_parsed) + len(state.args_parsed_negative)) > 0
            else necessary_joined
        )
        strong_where_clause = necessary_joined + (f" NOT {negative_field}" if n_fields else "")
    else:
        final_query = single_condition
        strong_where_clause = f"NOT {negative_field}" if n_fields else None

    return CompiledSearchQuery(
        final_query=final_query,
        strong_where_clause=strong_where_clause,
        positive_clauses=tuple(p_fields),
        negative_clauses=tuple(n_fields),
        necessary_clauses=tuple(necessary_unique),
        total_clause_count=len(p_fields) + len(n_fields) + len(necessary_unique),
    )


def build_search_debug_payload(
    state: ParsedSearchState,
    compiled: Optional[CompiledSearchQuery] = None,
    *,
    catch_all_fields: Optional[Sequence[str]] = None,
    catch_all_field_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    catch_all_fields_list = [str(value) for value in list(catch_all_fields or [])]
    catch_all_weights = {
        str(field): float(weight)
        for field, weight in dict(catch_all_field_weights or {}).items()
    }
    payload: Dict[str, object] = {
        "normalized_query_text": state.normalized_query_text,
        "positive_term_count": sum(len(seq) for seq in state.term_sequences),
        "negative_term_count": len(state.args_parsed_negative),
        "field_term_count": len(state.necessary_args),
        "term_sequences": [list(seq) for seq in state.term_sequences],
        "generated_bigram_windows": list(state.two_term_sequences),
        "generated_trigram_windows": list(state.three_term_sequences),
        "generated_bigram_window_count": len(state.two_term_sequences),
        "generated_trigram_window_count": len(state.three_term_sequences),
        "catch_all_fields": catch_all_fields_list,
        "catch_all_field_weights": catch_all_weights,
        "enable_sequence_expansion": state.enable_sequence_expansion,
        "max_bigram_windows": state.max_bigram_windows,
        "max_trigram_windows": state.max_trigram_windows,
    }
    if compiled is not None:
        payload.update(
            {
                "positive_clause_count": len(compiled.positive_clauses),
                "negative_clause_count": len(compiled.negative_clauses),
                "necessary_clause_count": len(compiled.necessary_clauses),
                "total_clause_count": compiled.total_clause_count,
                "strong_where_clause_present": bool(compiled.strong_where_clause),
            }
        )
    return payload


def parse_search(
    text_in: str,
    valid_fields: List[str],
    catch_all_fields: List[str] = ["text"],
    return_id_exclusions: bool = False,
    return_everything: bool = False,
    *,
    enable_sequence_expansion: bool = True,
    max_bigram_windows: Optional[int] = None,
    max_trigram_windows: Optional[int] = None,
    catch_all_field_weights: Optional[Dict[str, float]] = None,
) -> str:
    state = parse_search_state(
        text_in,
        valid_fields,
        enable_sequence_expansion=enable_sequence_expansion,
        max_bigram_windows=max_bigram_windows,
        max_trigram_windows=max_trigram_windows,
    )
    compiled = compile_search_state(
        state,
        catch_all_fields=catch_all_fields,
        catch_all_field_weights=catch_all_field_weights,
    )

    if return_id_exclusions:
        return compiled.final_query, compiled.strong_where_clause, list(state.id_exclusions)
    if return_everything:
        return (
            compiled.final_query,
            compiled.strong_where_clause,
            list(state.necessary_args),
            list(compiled.negative_clauses),
            list(compiled.positive_clauses),
            list(state.args_parsed),
            list(state.args_parsed_negative),
            [list(seq) for seq in state.term_sequences],
        )
    return compiled.final_query, compiled.strong_where_clause
