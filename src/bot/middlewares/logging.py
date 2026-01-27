from loguru import logger
from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import Update


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования входящих обновлений (Updates).
    Добавляет user_id и контекст события в логи Loguru.
    """

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:

        # Извлекаем пользователя из data
        user = data.get("event_from_user")
        user_id: int | str = user.id if user else "unknown"

        # Определяем тип действия для логов
        action = "unknown"

        if event.message and event.message.text:
            action = f"message: {event.message.text[:20]}"
        elif event.callback_query:
            action = f"callback: {event.callback_query.data}"

        log = logger.bind(user_id=user_id, update_id=event.update_id, action=action)

        log.info("Получено обновление")
        try:
            result = await handler(event, data)
            log.info("Обработка успешно завершена")
            return result
        except Exception:
            log.exception("Ошибка при обработке обновления")
            raise
