import sys
from loguru import logger


def setup_logger():
    """
    Настройка конфигурации логгера.
    Вызывается один раз при старте приложения.
    """
    # Удаляем стандартный обработчик, чтобы не дублировать логи
    logger.remove()

    # Формат логов:
    # Время | Уровень | Модуль:Строка - Сообщение
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 1. Вывод в консоль (stdout)
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True
    )

    # 2. Вывод в файл (с ротацией каждый день или по размеру 10 МБ)
    # Файлы будут лежать в папке logs/
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",  # Храним логи 7 дней
        compression="zip",   # Сжимаем старые логи
        format=log_format,
        level="DEBUG",       # В файл пишем всё, включая отладку
        encoding="utf-8"
    )

    logger.info("Логгер успешно настроен")
