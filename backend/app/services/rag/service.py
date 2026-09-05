"""RAG orchestration: retrieve -> generate -> persist. This is the single entry point the API route calls;
everything else in this package (retriever, prompt, generate) is a composable step it wires together.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.infrastructure.web_search import WebResult, search_web
from app.models import ChatConversation, ChatMessage, ChatRole, User
from app.services.rag.generate import generate_answer
from app.services.rag.retriever import RetrievedChunk, retrieve

HISTORY_TURNS = 6


@dataclass(frozen=True)
class SourceCitation:
    label: str
    source_type: str  # "product" | "review" | "web"
    source_id: UUID | None = None
    product_id: UUID | None = None
    similarity: float | None = None
    title: str | None = None   # web sources only
    url: str | None = None     # web sources only


@dataclass(frozen=True)
class ChatAnswer:
    conversation_id: UUID | None
    answer: str
    sources: list[SourceCitation]


def _resolve_conversation(db: Session, user: User, conversation_id: UUID | None, question: str) -> ChatConversation:
    """Fetch an owned conversation, or start a new one. Ownership is checked here so history can never leak across users."""
    if conversation_id is not None:
        conversation = db.scalar(select(ChatConversation).where(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id))
        if conversation is None:
            raise NotFoundError("Conversation not found")
        return conversation
    conversation = ChatConversation(user_id=user.id, title=question[:160])
    db.add(conversation)
    db.flush()
    return conversation


def _load_history(db: Session, conversation_id: UUID) -> list[tuple[str, str]]:
    """Most recent turns, oldest-first, for multi-turn context (e.g. "what about the second one?")."""
    rows = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at.desc()).limit(HISTORY_TURNS)).all()
    return [(row.role.value, row.content) for row in reversed(rows) if row.role != ChatRole.SYSTEM]


def _persist_turn(db: Session, conversation: ChatConversation, question: str, answer: str, cited: list[RetrievedChunk], cited_web: list[WebResult]) -> None:
    db.add(ChatMessage(conversation_id=conversation.id, role=ChatRole.USER, content=question))
    sources_metadata = [
        {"label": chunk.label, "source_type": chunk.source_type, "source_id": str(chunk.source_id), "product_id": str(chunk.product_id), "similarity": round(chunk.similarity, 4)}
        for chunk in cited
    ] + [
        {"label": result.label, "source_type": "web", "title": result.title, "url": result.url}
        for result in cited_web
    ]
    db.add(ChatMessage(conversation_id=conversation.id, role=ChatRole.ASSISTANT, content=answer, metadata_={"sources": sources_metadata}))
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()


def ask(db: Session, question: str, user: User | None = None, product_id: UUID | None = None, conversation_id: UUID | None = None) -> ChatAnswer:
    """Answer one shopper question, grounded in retrieved product/review context blended with a live web
    search - every answer draws on both, not just whichever one has something. Persists history only for
    signed-in users."""
    conversation = _resolve_conversation(db, user, conversation_id, question) if user is not None else None
    history = _load_history(db, conversation.id) if conversation is not None else None

    # pgvector retrieval and the Tavily web search are independent and each I/O-bound (DB round trip / HTTPS
    # call) - running them one after another added their latencies together for no reason. Safe to hand
    # `retrieve` to a worker thread even though SQLAlchemy Sessions aren't thread-safe for concurrent use:
    # nothing else touches `db` while `.result()` is blocked waiting on it, so only one thread ever has it
    # in hand at a time - just not always this function's own thread.
    with ThreadPoolExecutor(max_workers=2) as pool:
        chunks_future = pool.submit(retrieve, db, question, product_id=product_id)
        web_future = pool.submit(search_web, question)
        chunks = chunks_future.result()
        web_results = web_future.result()
    answer, cited, cited_web = generate_answer(question, chunks, web_results, history=history)

    if conversation is not None:
        _persist_turn(db, conversation, question, answer, cited, cited_web)

    sources = [
        SourceCitation(label=chunk.label, source_type=chunk.source_type, source_id=chunk.source_id, product_id=chunk.product_id, similarity=chunk.similarity)
        for chunk in cited
    ] + [
        SourceCitation(label=result.label, source_type="web", title=result.title, url=result.url)
        for result in cited_web
    ]
    return ChatAnswer(conversation_id=conversation.id if conversation else None, answer=answer, sources=sources)
