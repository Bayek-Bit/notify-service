import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class NotificationCreate(BaseModel):
    recipient_id: uuid.UUID
    title: str = Field(..., max_length=255)
    body: str = Field(..., min_length=1)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_id: uuid.UUID
    title: str
    body: str
    status: NotificationStatus
    is_read: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
