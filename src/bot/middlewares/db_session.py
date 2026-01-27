from loguru import logger
from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.infrastructure.database.repos.monitors_repo import MonitorRepository


class DbSessionMiddleware(BaseMiddleware):
    """
    Миддлварь для управления сессией подключения к БД.
    Берет async_sessionmaker из диспетчера, создает сессию и экземпляр MonitorRepository.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            # Прокидываем репозиторий в handler
            data["repo"] = MonitorRepository(session)

            try:
                # Вызываем хендлер
                result = await handler(event, data)

                # Коммит только если есть что коммитить
                if session.new or session.dirty or session.deleted:
                    await session.commit()

                return result

            except Exception:
                logger.exception("Необработанная ошибка в хэндлере; откат транзакции")
                # Если была ошибка — откатываем изменения
                await session.rollback()
                raise
