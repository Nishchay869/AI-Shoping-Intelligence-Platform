"""Request/response contracts for the RAG-backed shopping chat."""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    product_id: UUID | None = None
    conversation_id: UUID | None = None


class SourceCitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label: str
    source_type: str
    source_id: UUID | None = None
    product_id: UUID | None = None
    similarity: float | None = None
    title: str | None = None
    url: str | None = None


class ChatAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID | None
    answer: str
    sources: list[SourceCitationResponse]
