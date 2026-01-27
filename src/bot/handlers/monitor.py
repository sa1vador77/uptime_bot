from urllib.parse import urlparse

from loguru import logger

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy.exc import IntegrityError

from src.bot.states import MonitorAdd
from src.bot.lexicon import Texts, Buttons
from src.infrastructure.database.repos import MonitorRepository


monitor_router = Router()


@monitor_router.message(F.text == Buttons.START["menu_add_site"])
async def start_add_monitor(message: Message, state: FSMContext) -> None:
    """
    Инициация процесса добавления нового монитора.
    Переводит пользователя в состояние ожидания URL.
    """
    await message.answer(text=Texts.MySites.ADD_SITE)
    await state.set_state(MonitorAdd.waiting_for_url)


@monitor_router.message(StateFilter(MonitorAdd.waiting_for_url))
async def process_url(
    message: Message, state: FSMContext, repo: MonitorRepository
) -> None:
    """
    Валидация URL и сохранение в базу данных.
    Обрабатывает дубликаты и некорректный ввод.
    """
    user = message.from_user
    if user is None or message.text is None:
        await message.answer(text=Texts.MySites.INVALID_URL)
        return

    raw_url = message.text.strip()

    if not raw_url:
        await message.answer(text=Texts.MySites.INVALID_URL)
        return

    # Автоматическое добавление схемы, если отсутствует
    target_url = (
        raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
    )

    # Строгая валидация структуры URL
    try:
        parsed = urlparse(target_url)
    except ValueError:
        await message.answer(text=Texts.MySites.INVALID_URL)
        return

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or "." not in parsed.netloc
    ):
        await message.answer(text=Texts.MySites.INVALID_URL)
        return

    try:
        # Попытка сохранения в БД
        monitor = await repo.add_monitor(
            user_id=user.id,
            url=target_url,
            interval=300,
        )

        await message.answer(text=Texts.MySites.MONITOR_ADDED.format(monitor.url))
        await state.clear()

    except IntegrityError:
        # Обработка случая, если такой URL уже есть у пользователя
        await message.answer(text=Texts.MySites.ALREADY_ADDED)
        await state.clear()
        raise

    except Exception:
        logger.exception("Ошбика при добавлении сайта в монитор: url={}", target_url)
        await message.answer(text=Texts.MySites.UNEXPECTED_ERROR)
        await state.clear()
