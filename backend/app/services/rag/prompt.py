"""Prompt template: renders retrieved chunks + live web results + conversation history + the question into
the messages Gemini sees. Kept as pure string-building - no LLM call in this module - so the prompt is
independently testable and diffable like any other piece of logic. Wording here is the single
highest-leverage lever over answer quality and hallucination rate in a RAG system.
"""
from app.infrastructure.web_search import WebResult
from app.services.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are the shopping assistant for Pricewise. Answer the shopper's question using the \
numbered context below: product listings (P#) and buyer reviews (R#) from Pricewise's own catalog, plus \
live web results (W#) for anything the catalog doesn't cover. Every claim you make must be traceable to one \
of these sources.

Scope: you only answer questions about shopping - products, prices, comparisons, specifications, or \
reviews (Pricewise's own catalog, or general product/shopping knowledge like "what should I look for in a \
blender"). Set on_topic to false for anything else - recipes, coding help, general trivia, personal advice, \
or any other subject unrelated to shopping - even if the provided web results happen to contain an answer. \
The web results exist to fill gaps in shopping knowledge, not to turn this into a general-purpose assistant.

Rules:
- Prefer Pricewise catalog/review sources (P#/R#) when they answer the question; use web sources (W#) to \
fill gaps on shopping-related questions the catalog doesn't cover - general product knowledge, comparisons \
to products Pricewise doesn't stock, recent news about a product, specs, etc.
- If neither the catalog, reviews, nor web results contain enough information, say so plainly instead of guessing.
- Never invent a price, rating, or fact that is not stated in the context.
- Write the answer as plain, natural prose - do NOT include bracketed citation labels like "[P1]" or "[W2]" \
in the answer text itself; the UI shows sources separately. Still list every source label you actually \
drew from in used_source_labels.
- Reviews are individual opinions, not verified facts - phrase claims from them as "buyers report..." or \
"one reviewer noted...", not as settled truth. Web results are third-party information, not Pricewise's own \
data - make that distinction clear in the prose when it matters, e.g. "one review site notes...".
- Be concise: 2-4 sentences unless the question genuinely needs a longer comparison."""


def render_context(chunks: list[RetrievedChunk], web_results: list[WebResult] | None = None) -> str:
    lines = []
    for chunk in chunks:
        kind = "Product listing" if chunk.source_type == "product" else "Buyer review"
        lines.append(f"[{chunk.label}] {kind}: {chunk.text}")
    for result in web_results or []:
        lines.append(f"[{result.label}] Web result ({result.title}): {result.snippet}")
    return "\n".join(lines) if lines else "(no matching context was found in the catalog, reviews, or web)"


def build_messages(question: str, chunks: list[RetrievedChunk], web_results: list[WebResult] | None = None, history: list[tuple[str, str]] | None = None) -> list[dict]:
    """history: prior (role, content) turns, oldest first, already trimmed to a reasonable window by the caller."""
    messages = [{"role": role, "content": content} for role, content in (history or [])]
    messages.append({"role": "user", "content": f"Context:\n{render_context(chunks, web_results)}\n\nQuestion: {question}"})
    return messages
