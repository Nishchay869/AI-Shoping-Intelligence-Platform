"""Orchestration entry point: run one turn through the LangGraph agent, scoped to a persistent thread."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from uuid import uuid4
from app.core.exceptions import ServiceUnavailableError
from app.models import User
from app.services.assistant.graph import get_graph

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssistantSource:
    label: str
    title: str
    url: str


@dataclass(frozen=True)
class AssistantAnswer:
    thread_id: str
    answer: str
    tool_calls: list[str]  # names of tools invoked while answering - a simple "what did it check" transparency signal
    sources: list[AssistantSource]  # real (title, url) citations from this turn's web_search calls, if any


def _scoped_thread_id(user: User | None, key: str) -> str:
    """Namespace the LangGraph thread under the signed-in user, so one shopper can never resume another's
    conversation by guessing its thread_id - a different user reusing the same key just starts fresh."""
    return f"user:{user.id}:{key}" if user is not None else f"anon:{key}"


def ask(message: str, user: User | None = None, thread_id: str | None = None) -> AssistantAnswer:
    """Send one message to the assistant. Omit thread_id to start a new conversation; pass the one returned
    from a prior call to continue it - the LangGraph checkpointer resumes the full message history."""
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    key = thread_id or str(uuid4())
    config = {"configurable": {"thread_id": _scoped_thread_id(user, key)}}
    graph = get_graph()
    # `invoke()` returns the FULL accumulated thread state (checkpointer-backed), not just this turn's
    # messages - recording the length beforehand lets us slice out only what this turn actually added below,
    # so tool badges and web sources reflect this answer, not the whole conversation's history.
    prior_message_count = len(graph.get_state(config).values.get("messages", []))

    try:
        result = graph.invoke({"messages": [HumanMessage(content=message)]}, config)
    except Exception as exc:
        # One turn can call the chat model (graph.py's ChatOpenAI node) and/or a tool that does its own
        # OpenAI embeddings call (vector_store.search, used by 3 of tools.py's tools) - both are real,
        # unmocked external API calls that fail the same way a missing/exhausted/rate-limited key would.
        # Catching broadly here, at the single point every turn passes through, is deliberate: this graph has
        # multiple external-API surfaces (chat + tool-triggered embeddings), and a narrower catch at just one
        # of them would leave the other free to crash as an unhandled 500 exactly like this one did.
        logger.exception("assistant_graph_invocation_failed")
        raise ServiceUnavailableError("The AI assistant is temporarily unavailable") from exc

    new_messages = result["messages"][prior_message_count:]
    tool_calls = [call["name"] for message_ in new_messages if isinstance(message_, AIMessage) for call in (message_.tool_calls or [])]
    web_artifacts = [
        artifact
        for message_ in new_messages
        if isinstance(message_, ToolMessage) and message_.name == "web_search"
        for artifact in (message_.artifact or [])
    ]
    sources = [AssistantSource(label=f"W{i + 1}", title=artifact["title"], url=artifact["url"]) for i, artifact in enumerate(web_artifacts)]

    final_message = result["messages"][-1]
    # Gemini (via langchain_google_genai) returns content as a list of blocks (text + tool-call continuity
    # metadata under "extras"), not a plain string like older providers - .text extracts just the text parts
    # regardless of shape, where str(content) would dump the raw block list/dicts to the shopper.
    return AssistantAnswer(thread_id=key, answer=final_message.text, tool_calls=tool_calls, sources=sources)
