from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    message: str
    product_title: str
    is_read: bool
    created_at: datetime
