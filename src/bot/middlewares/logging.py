from loguru import logger
from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования входящих обновлений (Updates).
    Добавляет user_id и контекст события в логи Loguru.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        # Извлекаем пользователя из data
        user = data.get("event_from_user")
        user_id = user.id if user else "unknown"

        # Определяем тип действия для логов
        action = "unknown"
        update_id = "unknown"

        if isinstance(event, Update):
            update_id = event.update_id
            if event.message and event.message.text:
                action = (
                    f"message: {event.message.text[:20]}"  # Обрезаем длинные сообщения
                )
            elif event.callback_query:
                action = f"callback: {event.callback_query.data}"

        with logger.contextualize(user_id=user_id, update_id=update_id, action=action):
            logger.info("Получено обновление")
            try:
                result = await handler(event, data)
                logger.info("Обработка успешно завершена")
                return result
            except Exception:
                logger.exception("Ошибка при обработке обновления")
                raise
