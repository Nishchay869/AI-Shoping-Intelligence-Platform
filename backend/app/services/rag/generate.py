"""Answer generation: the final LLM call. Uses structured output so the model must explicitly declare which
source labels it actually used - a cheap, reliable grounding check that doesn't depend on regex-parsing the
prose answer for citation brackets, and a second line of defense (alongside the prompt's own instruction)
against answering when the retrieved context doesn't cover the question.
"""
import json
from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError
from app.infrastructure.llm import create_message
from app.infrastructure.web_search import WebResult
from app.services.rag.prompt import SYSTEM_PROMPT, build_messages
from app.services.rag.retriever import RetrievedChunk

NOT_ENOUGH_CONTEXT_MESSAGE = "I don't have enough information in the catalog, reviews, or web to answer that confidently."
OFF_TOPIC_MESSAGE = "I'm Pricewise's shopping assistant, so I can only help with product questions, price comparisons, and reviews - that's outside what I can answer here."

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "on_topic": {"type": "boolean", "description": "True only if the question is about shopping - products, prices, comparisons, specs, or reviews. False for anything else (recipes, coding help, general trivia, personal advice, etc.), even if the provided web results happen to cover it."},
        "can_answer": {"type": "boolean", "description": "True only if on_topic is true AND the provided context actually supports an answer."},
        "answer": {"type": "string", "description": "The answer as plain prose, with no bracketed citation labels in the text. Empty if on_topic or can_answer is false."},
        "used_source_labels": {"type": "array", "items": {"type": "string"}, "description": "Every source label (e.g. 'P1', 'R3', 'W2') actually drawn from to write the answer, even though the answer text itself doesn't mention them."},
    },
    "required": ["on_topic", "can_answer", "answer", "used_source_labels"],
    "additionalProperties": False,
}


def generate_answer(question: str, chunks: list[RetrievedChunk], web_results: list[WebResult] | None = None, history: list[tuple[str, str]] | None = None) -> tuple[str, list[RetrievedChunk], list[WebResult]]:
    """Returns the final answer text and the subset of catalog chunks and web results the model actually cited."""
    web_results = web_results or []
    if not chunks and not web_results:
        return NOT_ENOUGH_CONTEXT_MESSAGE, [], []

    settings = get_settings()
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=build_messages(question, chunks, web_results, history),
        output_config={"format": {"type": "json_schema", "schema": ANSWER_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to answer this question")

    payload = json.loads(response.content[0].text)
    if not payload["on_topic"]:
        return OFF_TOPIC_MESSAGE, [], []
    if not payload["can_answer"] or not payload["answer"].strip():
        return NOT_ENOUGH_CONTEXT_MESSAGE, [], []

    used_labels = set(payload["used_source_labels"])
    cited_chunks = [chunk for chunk in chunks if chunk.label in used_labels]
    cited_web = [result for result in web_results if result.label in used_labels]
    return payload["answer"], cited_chunks, cited_web
