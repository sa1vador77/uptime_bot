import sys
import json
import logging
from typing import Any
from pathlib import Path

from loguru import logger as _logger


def _serialize_extra(record: dict[str, Any]) -> str:
    """Форматирует extra параметры для логов.

    Args:
        record: Loguru record с информацией о логе.

    Returns:
        Строка с отформатированными параметрами или пустая строка.
    """
    extra = record["extra"]
    if not extra:
        return ""
    # Конвертируем все значения в строки
    items = [f"{k}: {repr(v)}" for k, v in extra.items()]
    return " -> " + " | ".join(items)


def _format_console(record: dict[str, Any]) -> str:
    """Форматирует лог для консоли с цветами.

    Args:
        record: Loguru record.

    Returns:
        Отформатированная строка для вывода.
    """
    extra_str = _serialize_extra(record)

    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
        f"<yellow>{extra_str}</yellow>\n"
    )


def _format_file(record: dict[str, Any]) -> str:
    """Форматирует лог для файла (без цветов).

    Args:
        record: Loguru record.

    Returns:
        Отформатированная строка для вывода.
    """
    extra_str = _serialize_extra(record)

    return (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
        f"{extra_str}\n"
    )


def _format_json(record: dict[str, Any]) -> str:
    """Форматирует лог в JSON для ошибок.

    Args:
        record: Loguru record.

    Returns:
        JSON строка.
    """
    payload = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "location": f"{record['name']}:{record['function']}:{record['line']}",
        "extra": record["extra"],
    }
    return json.dumps(payload, ensure_ascii=False, default=str) + "\n"


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Получаем level
        try:
            level: str | int = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Ищем, откуда вызван logging.info()
        frame = logging.currentframe()
        depth = 2

        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Отправляем в loguru с правильной глубиной
        _logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


_CONFIGURED = False


def configure_logger() -> None:
    """Конфигурирует loguru с поддержкой extra параметров.

    Удаляет дефолтный handler и добавляет:
    - Console: цветной вывод в stderr
    - App log: все логи в файл с параметрами
    - Errors JSON: ошибки в JSON формате
    """
    global _CONFIGURED

    if _CONFIGURED:
        return
    _CONFIGURED = True
    # Удаляем дефолтный handler
    _logger.remove()

    # Console handler
    _logger.add(
        sink=sys.stderr,
        format=_format_console,
        level="DEBUG",
        colorize=True,
    )

    # File handler для app логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    _logger.add(
        sink=log_dir / "app.log",
        format=_format_file,
        level="DEBUG",
        rotation="100 MB",
        retention="7 days",
        compression="zip",
    )

    # File handler для ошибок (ERROR+ в JSON)
    _logger.add(
        sink=log_dir / "errors.json",
        format=_format_json,
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


# Конфигурируем при импорте
configure_logger()
# Экспортируем логгер
logger = _logger
