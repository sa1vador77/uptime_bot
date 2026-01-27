from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import MonitorModel


class MonitorRepository:
    """
    Репозиторий для работы с таблицей monitors.
    Инкапсулирует SQL-запросы.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_monitor(
        self,
        url: str,
        user_id: int,
        interval: int = 300,
    ) -> MonitorModel:
        """
        Добавляет новый монитор в базу данных.
        """
        monitor = MonitorModel(
            user_id=user_id,
            url=url,
            check_interval=interval,
            is_active=True,
        )
        self.session.add(monitor)
        await self.session.flush()
        return monitor

    async def get_user_monitors(self, user_id: int) -> Sequence[MonitorModel]:
        """
        Возвращает список всех мониторов пользователя.
        """
        stmt = (
            select(MonitorModel)
            .where(MonitorModel.user_id == user_id)
            .order_by(MonitorModel.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_monitor_by_id(self, monitor_id: int) -> MonitorModel | None:
        """
        Получает монитор по ID.
        """
        return await self.session.get(MonitorModel, monitor_id)

    async def delete_monitor(self, monitor_id: int, user_id: int) -> bool:
        """
        Удаляет монитор. Проверяет, что монитор принадлежит пользователю.
        Возвращает True, если удаление прошло успешно.
        """
        stmt = delete(MonitorModel).where(
            MonitorModel.id == monitor_id,
            MonitorModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0

    async def get_active_monitors(self) -> Sequence[MonitorModel]:
        """
        Возвращает ВСЕ активные мониторы для планировщика задач.
        """
        stmt = select(MonitorModel).where(MonitorModel.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()
