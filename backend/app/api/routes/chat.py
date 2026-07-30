from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_optional, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.chat import AskRequest, ChatAnswerResponse
from app.services.rag.service import ask

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatAnswerResponse, dependencies=[Depends(rate_limit(20, 60))])
def ask_shopping_assistant(payload: AskRequest, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)) -> ChatAnswerResponse:
    """Answer a shopper's question via RAG over the product catalog and reviews; persists history when signed in."""
    result = ask(db, payload.message, user=user, product_id=payload.product_id, conversation_id=payload.conversation_id)
    return ChatAnswerResponse.model_validate(result)
