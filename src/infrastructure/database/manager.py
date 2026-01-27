from loguru import logger

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.config import settings


class DatabaseManager:
    """
    Класс для управления подключением к базе данных.
    Инкапсулирует создание движка (engine) и фабрики сессий.
    """

    def __init__(self, db_url: str, echo: bool = False) -> None:
        # Создаем асинхронный движок
        # echo=True будет выводить все SQL запросы в консоль (полезно для отладки)
        self.engine = create_async_engine(
            db_url,
            echo=echo,
        )

        # Фабрика сессий. expire_on_commit=False чтобы избежать проблем с “expired attributes”
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def health_check(self) -> bool:
        """Проверяет соединение с БД, выполняя простой запрос."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Подключение к базе данных: OK")
            return True
        except Exception:
            logger.exception("Ошибка подключения к БД")
            return False

    async def close(self) -> None:
        """Корректное закрытие соединения с БД при остановке бота."""
        await self.engine.dispose()


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager(
    db_url=settings.DB_URL,
    echo=settings.DB_ECHO,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор сессий.
    Возвращает асинхронный генератор, который yield-ит сессию.
    """
    async with db_manager.session_maker() as session:
        yield session
