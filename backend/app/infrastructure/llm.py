"""Shared Gemini client + an Anthropic-shaped call wrapper for every LLM-backed service (recommendations,
review summarization, receipt scanning, RAG chat). Kept as a compatibility shim - deliberately - so moving
providers didn't require touching any of those 4 services' prompts, schemas, or response-reading code: a
call site still does create_message(model=..., max_tokens=..., system=..., messages=[...],
output_config=...) and reads response.stop_reason / response.content[0].text exactly as before Gemini.
"""
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)
_ROLE_MAP = {"user": "user", "assistant": "model"}


@lru_cache
def _client() -> genai.Client:
    """One process-lifetime client, not a fresh instance per call - the google-genai SDK's own retry logic
    reuses this object's internal httpx client across attempts, and a throwaway instance gets garbage
    collected (closing that httpx client) mid-retry, raising "Cannot send a request, as the client has been
    closed." (a known SDK issue: googleapis/python-genai#1763). Mirrors embeddings.py's Voyage client, which
    caches for the same reason."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ServiceUnavailableError("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.gemini_api_key)


def _to_gemini_schema(schema: Any) -> Any:
    """Recursively translate a schema written for Anthropic's JSON-Schema-based structured output into
    Gemini's OpenAPI-subset format:
    - `"type": [X, "null"]` (every nullable field in this codebase's schemas) becomes `"type": X,
      "nullable": true`.
    - `additionalProperties` is dropped entirely - confirmed live against the real API (not just docs) that
      it rejects this field outright ("Unknown name additional_properties... Cannot find field"), regardless
      of value. Harmless to drop: application code only ever reads the specific keys it expects out of the
      model's response and already ignores anything else.
    Everything else (properties/required/enum/items) passes through unchanged."""
    if isinstance(schema, dict):
        result = {key: _to_gemini_schema(value) for key, value in schema.items() if key != "additionalProperties"}
        type_field = result.get("type")
        if isinstance(type_field, list) and "null" in type_field:
            non_null = [t for t in type_field if t != "null"]
            result["type"] = non_null[0] if len(non_null) == 1 else non_null
            result["nullable"] = True
        return result
    if isinstance(schema, list):
        return [_to_gemini_schema(item) for item in schema]
    return schema


@dataclass(frozen=True)
class _TextBlock:
    text: str


@dataclass(frozen=True)
class _Message:
    stop_reason: str
    content: list[_TextBlock]


def create_message(*, model: str, max_tokens: int, system: str, messages: list[dict[str, str]], output_config: dict[str, Any]) -> _Message:
    """Anthropic-shaped call, Gemini underneath. Any real API-level failure (billing, rate limits,
    connectivity, a Gemini-side outage) - or any unexpected response shape - becomes a clean
    ServiceUnavailableError rather than an unhandled 500."""
    contents = [
        types.Content(role=_ROLE_MAP[message["role"]], parts=[types.Part.from_text(text=message["content"])])
        for message in messages
    ]
    try:
        response = _client().models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
                response_schema=_to_gemini_schema(output_config["format"]["schema"]),
            ),
        )
        candidates = response.candidates or []
        if not candidates or candidates[0].finish_reason != types.FinishReason.STOP:
            return _Message(stop_reason="refusal", content=[_TextBlock(text="")])
        return _Message(stop_reason="end_turn", content=[_TextBlock(text=response.text)])
    except ServiceUnavailableError:
        raise
    except Exception as exc:
        logger.exception("gemini_api_call_failed")
        raise ServiceUnavailableError("The AI service is temporarily unavailable") from exc


_IMAGE_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "is_genuine_product_photo": {"type": "boolean", "description": "True only if the product's actual physical shape/design is clearly and recognizably visible (e.g. a clean front+back render of the same device is fine). False for badges, trust/award icons, logos, banners, or generic marketing graphics. False for collage/listicle-style composites showing other unrelated products alongside it, even if the named product is the main subject. False for launch/teaser announcement cards that show mostly brand name or model text over an abstract/stylized background rather than the device itself. False for close-up crops of just a color/texture/material swatch where the device's actual shape isn't identifiable."},
                },
                "required": ["index", "is_genuine_product_photo"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def verify_product_photos(candidates: list[tuple[str, bytes, str]]) -> list[bool]:
    """Vision check: for each (title, image_bytes, mime_type), asks Gemini whether the image is genuinely a
    product photo of that item. Exists because URL-pattern filtering alone let real defects through: Amazon's
    site-wide "Amazon's Choice" trust-badge graphic (living at a normal-looking /images/I/ path with no
    suspicious filename) was shown as the product photo for several unrelated laptops, and a phone-wallpaper
    mockup blog image (a tight crop of just the colorful lock-screen, no device body visible) was shown as an
    iPhone's product photo. Retries once, then fails closed (every candidate rejected) rather than open -
    a missing image is an honest placeholder; a wrong one actively misleads a shopper, so an infrastructure
    hiccup here should never risk showing that."""
    if not candidates:
        return []
    settings = get_settings()
    parts: list[types.Part] = []
    for i, (title, image_bytes, mime_type) in enumerate(candidates):
        parts.append(types.Part.from_text(text=f"Image {i}: candidate photo for '{title}'"))
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    for attempt in range(2):
        try:
            response = _client().models.generate_content(
                model=settings.recommendation_model,
                contents=[types.Content(role="user", parts=parts)],
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "For each numbered image, decide whether the product's actual physical shape and "
                        "design is clearly and recognizably visible - real photography or a manufacturer "
                        "packshot showing that device (multiple angles of the same device, like a front+back "
                        "render, are fine). Reject site-wide trust badges, award icons, logos, banners, "
                        "screenshots of unrelated UI, generic marketing graphics, and listicle-style collages "
                        "that mix in other unrelated products - even if the named product is the largest or "
                        "most prominent element. Also reject launch/teaser announcement cards that show "
                        "mostly a brand name or model name as text over an abstract or stylized background "
                        "rather than the device; close-up crops of just a color/texture/material swatch where "
                        "you can't actually tell what the device looks like; and crops of just a screen/"
                        "display showing wallpaper, a lock screen, or other on-screen content without enough "
                        "of the device's outer body or edges visible to confirm its actual shape."
                    ),
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                    response_schema=_to_gemini_schema(_IMAGE_VERDICT_SCHEMA),
                ),
            )
            result_candidates = response.candidates or []
            if not result_candidates or result_candidates[0].finish_reason != types.FinishReason.STOP:
                continue
            payload = json.loads(response.text)
            verdicts = {item["index"]: item["is_genuine_product_photo"] for item in payload["results"]}
            return [verdicts.get(i, False) for i in range(len(candidates))]
        except Exception:
            logger.exception("image_verification_failed attempt=%d", attempt)
    return [False] * len(candidates)
