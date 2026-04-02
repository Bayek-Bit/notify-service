import uuid


class NotificationError(Exception):
    """Базовое исключение для уведомлений.

    Важно: это доменная ошибка (не FastAPI), но она несет HTTP-метаданные
    (`status_code`, `detail`), чтобы API-слой мог корректно отдать ответ.
    """

    status_code: int = 500
    detail: str = "Internal Server Error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotificationNotFoundError(NotificationError):
    """Уведомление не найдено."""

    def __init__(self, notification_id: uuid.UUID):
        self.notification_id = notification_id
        super().__init__(f"Notification {notification_id} not found")
        # backward-compatible attributes (если где-то ещё используется)
        self.message = self.detail
        self.status_code = 404


class UserNotFoundError(NotificationError):
    """Пользователь не найден."""

    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")
        # backward-compatible attributes (если где-то ещё используется)
        self.message = self.detail
        self.status_code = 404
