import uuid
from datetime import datetime, timezone

from src.api.v1.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
)


class NotificationService:
    async def send_notification(
        self, notification: NotificationCreate
    ) -> NotificationResponse:
        return NotificationResponse(
            id=uuid.uuid4(),
            recipient_id=notification.recipient_id,
            title=notification.title,
            body=notification.body,
            status=NotificationStatus.PENDING,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
