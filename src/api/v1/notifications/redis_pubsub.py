import json
import redis.asyncio as redis
from src.api.v1.notifications.logging_service import logger


class RedisPubSubManager:
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.redis_url = url
        self._redis: redis.Redis | None = None

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Redis Pub/Sub успешно подключен")

    async def publish(self, channel: str, message: dict):
        """Публикация сообщения в канал для всех инстансов бэкенда"""
        if not self._redis:
            await self.connect()

        # default=str нужен для корректной сериализации UUID
        payload = json.dumps(message, default=str)
        assert self._redis is not None, "Redis not connected"
        await self._redis.publish(channel, payload)
        logger.info(f" [REDIS] Сообщение опубликовано в канал {channel}")


# Глобальный инстанс
redis_manager = RedisPubSubManager()
