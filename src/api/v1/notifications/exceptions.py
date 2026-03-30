import uuid


class NotificationError(Exception):
    """Базовое исключение для уведомлений."""


class NotificationNotFoundError(NotificationError):
    """Уведомление не найдено."""

    def __init__(self, notification_id: uuid.UUID):
        self.notification_id = notification_id
        self.message = f"Notification {notification_id} not found"
        super().__init__(self.message)


class UserNotFoundError(NotificationError):
    """Пользователь не найден."""

    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        self.message = f"User {user_id} not found"
        super().__init__(self.message)
