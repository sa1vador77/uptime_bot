from datetime import datetime

from sqlalchemy import BigInteger, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models import BaseModel


class MonitorModel(BaseModel):
    """
    Модель задачи мониторинга.
    Хранит информацию о том, какой URL проверять и кому сообщать результат.
    """

    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ID пользователя Telegram
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # URL для проверки
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Интервал проверки в секундах
    check_interval: Mapped[int] = mapped_column(default=300)

    # Активен ли мониторинг
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Дата создания записи (автоматически ставится базой данных)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Monitor(id={self.id}, user={self.user_id}, url='{self.url}')>"
