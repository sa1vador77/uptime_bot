from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.infrastructure.database.repos.monitors_repo import MonitorRepository


class DbSessionMiddleware(BaseMiddleware):
    """
    Миддлварь для управления сессией подключения к БД.
    Берет async_sessionmaker из диспетчера, создает сессию и экземпляр MonitorRepository.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            # Создаем репозиторий с текущей сессией
            repo = MonitorRepository(session)

            # Прокидываем репозиторий в handler
            data["repo"] = repo

            try:
                # Вызываем хендлер
                result = await handler(event, data)

                # Если хендлер отработал без ошибок — коммитим транзакцию
                await session.commit()
                return result

            except Exception:
                # Если была ошибка — откатываем изменения
                await session.rollback()
                raise
