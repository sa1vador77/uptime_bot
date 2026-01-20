import asyncio

from loguru import logger
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from src.bot.lexicon import Texts
from src.infrastructure.database.manager import get_session
from src.infrastructure.network.client import NetworkClient
from src.infrastructure.database.repos import MonitorRepository


async def monitoring_task(bot: Bot):
    """
    Задача планировщика: проверка всех активных мониторов.
    Выполняется в фоне с заданным интервалом.
    """
    logger.debug("Запуск цикла мониторинга...")
    client = NetworkClient(timeout=15)

    # Открываем новую сессию для каждой итерации задачи
    async for session in get_session():
        repo = MonitorRepository(session)

        # 1. Загрузка всех активных задач
        active_monitors = await repo.get_active_monitors()
        if not active_monitors:
            return

        # 2. Выполнение проверок
        tasks = [client.check_url(monitor.url) for monitor in active_monitors]
        results = await asyncio.gather(*tasks)

        # 3. Обработка результатов и отправка уведомлений
        for monitor, result in zip(active_monitors, results):
            # Логика: если сайт лежит ИЛИ SSL истекает < 7 дней -> шлем алерт

            # А. Сайт недоступен
            if not result.is_up:
                message_text = Texts.MySites.UNAVAILABLE.format(
                    monitor.url,
                    f"{result.error or f'Status {result.status_code}'}",
                )
                await _send_alert(bot, monitor.user_id, message_text)
                continue

            # Б. Проблема с SSL (осталось меньше 7 дней)
            if result.ssl_days_left is not None and result.ssl_days_left < 7:
                message_text = Texts.MySites.CERTIFICATE_EXPIRE.format(
                    monitor.url,
                    result.ssl_expires_at.strftime("%Y-%m-%d"),
                    result.ssl_days_left,
                )
                await _send_alert(bot, monitor.user_id, message_text)

    logger.debug("Цикл завершен", checked_urls=len(active_monitors))


async def _send_alert(bot: Bot, user_id: int, text: str):
    """
    Безопасная отправка сообщения с подавлением ошибок (если юзер заблочил бота).
    """
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except TelegramAPIError as e:
        logger.warning(f"Не удалось отправить алерт пользователю {user_id}: {e}")
