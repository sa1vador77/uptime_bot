from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Глобальные настройки приложения.
    Валидируются при запуске через Pydantic.
    """
    
    # Telegram
    BOT_TOKEN: SecretStr
    ADMIN_IDS: list[int]  # Ожидает формат JSON в .env: ADMIN_IDS=[123, 456]

    # Database
    DB_URL: str = "sqlite+aiosqlite:///uptime.db"
    DB_ECHO: bool = False
    
    # Monitoring defaults
    DEFAULT_CHECK_INTERVAL: int = 300  # 5 минут
    REQUEST_TIMEOUT: int = 10          # Таймаут HTTP запроса в секундах

    # Настройки загрузки
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорировать лишние переменные в .env
    )

settings = Settings()
