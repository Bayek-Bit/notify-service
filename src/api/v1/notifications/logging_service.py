import logging
from typing import Any


class LoggingService:
    def __init__(self, log_file: str = "logs/app.log"):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логирование информационного сообщения"""
        if args:
            message = message % args  # форматирование в стиле %
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.info(message)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логирование ошибки"""
        if args:
            message = message % args
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.error(message)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логирование предупреждения"""
        if args:
            message = message % args
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.warning(message)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Логирование критической ошибки"""
        if args:
            message = message % args
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.critical(message)


logger = LoggingService()
