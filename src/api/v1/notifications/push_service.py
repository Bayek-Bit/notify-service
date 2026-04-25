from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.schemas import NotificationTask


async def send_push_notification(task: NotificationTask) -> bool:
    """
    Заглушка для отправки Push-уведомления.
    В будущем здесь будет интеграция с FCM, APNS или другим провайдером.
    """
    logger.info(
        f" [PUSH] Отправка уведомления пользователю {task.recipient_id}: {task.title}"
    )
    # Имитируем успешную отправку
    return True
