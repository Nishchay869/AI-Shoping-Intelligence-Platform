from fastapi import APIRouter, Depends
from app.api.deps import get_current_user_optional, rate_limit
from app.models import User
from app.schemas.assistant import AssistantAskRequest, AssistantAskResponse
from app.services.assistant.service import ask

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantAskResponse, dependencies=[Depends(rate_limit(20, 60))])
def chat_with_assistant(payload: AssistantAskRequest, user: User | None = Depends(get_current_user_optional)) -> AssistantAskResponse:
    """Talk to the LangGraph-orchestrated shopping assistant - compares, explains specs, suggests alternatives,
    and recommends products via tool calls, with persistent per-thread memory across turns."""
    result = ask(payload.message, user=user, thread_id=payload.thread_id)
    return AssistantAskResponse(thread_id=result.thread_id, answer=result.answer, tool_calls=result.tool_calls, sources=result.sources)
