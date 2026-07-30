"""Unit tests: the JSON-Schema -> Gemini-schema translator in infrastructure/llm.py. No DB, no network -
pure function, but this is the one real behavioral risk in the Anthropic->Gemini migration (Gemini's
response_schema is an OpenAPI-3.0 subset, not full JSON Schema)."""
from app.infrastructure.llm import _to_gemini_schema


def test_nullable_type_union_becomes_nullable_flag() -> None:
    schema = {"type": ["string", "null"]}
    assert _to_gemini_schema(schema) == {"type": "string", "nullable": True}


def test_non_nullable_type_is_unchanged() -> None:
    schema = {"type": "integer"}
    assert _to_gemini_schema(schema) == {"type": "integer"}


def test_required_passes_through_unchanged() -> None:
    schema = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
    assert _to_gemini_schema(schema) == schema


def test_additional_properties_is_dropped() -> None:
    """The live Gemini API rejects this field outright ("Unknown name additional_properties... Cannot find
    field"), confirmed against the real API, not just docs - so it must never reach the wire, regardless of
    its value."""
    schema = {"type": "object", "properties": {"a": {"type": "string"}}, "additionalProperties": False}
    result = _to_gemini_schema(schema)
    assert "additionalProperties" not in result
    assert result == {"type": "object", "properties": {"a": {"type": "string"}}}


def test_additional_properties_is_dropped_at_every_nesting_level() -> None:
    schema = {"type": "object", "additionalProperties": False, "properties": {"items": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"x": {"type": "string"}}}}}}
    result = _to_gemini_schema(schema)
    assert "additionalProperties" not in result
    assert "additionalProperties" not in result["properties"]["items"]["items"]


def test_nested_nullable_fields_are_translated_recursively() -> None:
    schema = {
        "type": "object",
        "properties": {
            "store_name": {"type": ["string", "null"]},
            "items": {"type": "array", "items": {"type": "object", "properties": {"price": {"type": ["number", "null"]}}}},
        },
    }
    result = _to_gemini_schema(schema)
    assert result["properties"]["store_name"] == {"type": "string", "nullable": True}
    assert result["properties"]["items"]["items"]["properties"]["price"] == {"type": "number", "nullable": True}


def test_multiple_non_null_types_in_union_keep_a_list() -> None:
    """Edge case: a union of more than one real type plus null - rare in this codebase's schemas, but the
    translator must not silently drop one of the real types."""
    schema = {"type": ["string", "integer", "null"]}
    result = _to_gemini_schema(schema)
    assert result["nullable"] is True
    assert set(result["type"]) == {"string", "integer"}
