import asyncio
from typing import Any

from loguru import logger
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from src.bot.lexicon import Texts
from src.infrastructure.database.manager import db_manager
from src.infrastructure.network.client import NetworkClient
from src.infrastructure.database.repos import MonitorRepository


async def monitoring_task(bot: Bot) -> None:
    """
    Задача планировщика: проверка всех активных мониторов.
    Выполняется в фоне с заданным интервалом.
    """
    logger.debug("Запуск цикла мониторинга...")
    client = NetworkClient(timeout=15)

    try:
        async with db_manager.session_maker() as session:
            repo = MonitorRepository(session)

            # 1. Загрузка всех активных задач
            active_monitors = await repo.get_active_monitors()
            if not active_monitors:
                logger.debug("Не найдено активных сайтов для мониторинга")
                return

            # 2. Выполнение проверок
            checks = [client.check_url(monitor.url) for monitor in active_monitors]
            results: list[Any] = await asyncio.gather(*checks, return_exceptions=True)

            # 3. Обработка результатов и отправка уведомлений
            for monitor, item in zip(active_monitors, results):
                if isinstance(item, Exception):
                    message_text = Texts.MySites.UNAVAILABLE.format(
                        monitor.url, str(item)
                    )
                    await _send_alert(bot, monitor.user_id, message_text)
                    continue

                result = item

                if not result.is_up:
                    message_text = Texts.MySites.UNAVAILABLE.format(
                        monitor.url,
                        result.error or f"Status {result.status_code}",
                    )
                    await _send_alert(bot, monitor.user_id, message_text)
                    continue

                if result.ssl_days_left is not None and result.ssl_days_left < 7:
                    message_text = Texts.MySites.CERTIFICATE_EXPIRE.format(
                        monitor.url,
                        (
                            result.ssl_expires_at.strftime("%Y-%m-%d")
                            if result.ssl_expires_at
                            else "unknown"
                        ),
                        result.ssl_days_left,
                    )
                await _send_alert(bot, monitor.user_id, message_text)

        logger.debug("Цикл завершен", checked_urls=len(active_monitors))

    finally:
        await client.close()


async def _send_alert(bot: Bot, user_id: int, text: str) -> None:
    """
    Безопасная отправка сообщения с подавлением ошибок (если юзер заблочил бота).
    """
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except TelegramAPIError as e:
        logger.warning("Не удалось отправить алерт пользователю", user_id, str(e))
