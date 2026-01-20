import asyncio
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.core.logger import configure_logger
from src.bot.middlewares import DbSessionMiddleware, LoggingMiddleware
from src.infrastructure.database.manager import db_manager
from src.infrastructure.scheduler.tasks import monitoring_task

from src.bot.handlers import (
    user_router,
    monitor_router,
)


async def main():
    # 1. Настройка логгера
    configure_logger()
    logger.info("Запуск приложения...")

    # 2. Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # 3. Инициализация диспетчера
    dp = Dispatcher()

    # 4. Подключение Middleware
    # Передаем фабрику сессий в мидлварь
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.middleware(DbSessionMiddleware(session_factory=db_manager.session_maker))

    # 5. Регистрация роутеров
    dp.include_routers(
        user_router,
        monitor_router,
    )

    scheduler = AsyncIOScheduler()
    # Добавляем задачу (раз в 60 секунд)
    scheduler.add_job(monitoring_task, "interval", seconds=60, args=[bot])
    scheduler.start()
    # 6. Запуск polling
    try:
        # Удаляем вебхук и дропаем накопившиеся апдейты (чтобы бот не отвечал на старое)
        await bot.delete_webhook(drop_pending_updates=True)
        await db_manager.health_check()
        logger.info("Бот начал прослушивание событий")
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка приложения...")
        # Закрываем соединение с БД при выходе
        await db_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
