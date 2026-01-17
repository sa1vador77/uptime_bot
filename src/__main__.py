import asyncio
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.core.config import settings
from src.core.logger import setup_logger
from src.infrastructure.database.manager import db_manager
from src.bot.middlewares.db_session import DbSessionMiddleware
# from src.bot.handlers import user_router


async def main():
    # 1. Настройка логгера
    setup_logger()
    logger.info("Запуск приложения...")

    # 2. Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # 3. Инициализация диспетчера
    dp = Dispatcher()

    # 4. Подключение Middleware
    # Передаем фабрику сессий в мидлварь
    dp.update.middleware(DbSessionMiddleware(session_factory=db_manager.session_maker))

    # 5. Регистрация роутеров
    # dp.include_router(user_router)

    # 6. Запуск polling
    try:
        # Удаляем вебхук и дропаем накопившиеся апдейты (чтобы бот не отвечал на старое)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот начал прослушивание событий")
        await db_manager.health_check()
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка приложения...")
        # Закрываем соединение с БД при выходе
        await db_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")
