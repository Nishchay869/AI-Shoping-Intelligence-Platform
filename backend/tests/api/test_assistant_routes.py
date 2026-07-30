"""API tests: /api/v1/assistant/chat. The full LangGraph agent needs a real OPENAI_API_KEY this environment
doesn't have, so these use build_graph()'s overridable model_node (see graph.py's own docstring: it exists
specifically so tests can substitute a scripted fake model without a real API key)."""
from unittest.mock import patch

from langchain_core.messages import AIMessage


def _fake_model_node_answering(text: str):
    def _node(state):
        return {"messages": [AIMessage(content=text)]}
    return _node


def _fake_model_node_raising(exc: Exception):
    def _node(state):
        raise exc
    return _node


def test_chat_returns_the_models_answer(client) -> None:
    from app.services.assistant.graph import build_graph

    fake_graph = build_graph(model_node=_fake_model_node_answering("The Sony WH-1000XM5 has the best battery life."))
    with patch("app.services.assistant.service.get_graph", return_value=fake_graph):
        response = client.post("/api/v1/assistant/chat", json={"message": "which headphones last longest?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "The Sony WH-1000XM5 has the best battery life."


def test_chat_when_the_model_call_fails_is_service_unavailable_not_a_crash(client) -> None:
    """A real OpenAI API-level failure (quota, rate limit, connectivity, an OpenAI-side outage) from either
    the chat model node or a tool's own embeddings call - distinct from a missing API key - must surface as
    a clean 503, never an unhandled 500. This is the exact bug hit live: a real account with expired quota
    raised openai.RateLimitError, uncaught, through this same call path."""
    from app.services.assistant.graph import build_graph

    fake_graph = build_graph(model_node=_fake_model_node_raising(RuntimeError("insufficient_quota")))
    with patch("app.services.assistant.service.get_graph", return_value=fake_graph):
        response = client.post("/api/v1/assistant/chat", json={"message": "compare iphone 11 and iphone 16"})
    assert response.status_code == 503
