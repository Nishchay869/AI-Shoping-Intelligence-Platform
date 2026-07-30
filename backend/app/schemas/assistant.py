"""Request/response contracts for the LangGraph-based shopping assistant."""
from pydantic import BaseModel, ConfigDict, Field


class AssistantAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None


class AssistantSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label: str
    title: str
    url: str


class AssistantAskResponse(BaseModel):
    thread_id: str
    answer: str
    tool_calls: list[str]
    sources: list[AssistantSourceResponse]
