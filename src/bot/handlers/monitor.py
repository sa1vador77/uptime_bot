from urllib.parse import urlparse

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy.exc import IntegrityError

from src.bot.states import MonitorAdd
from src.bot.lexicon import Texts, Buttons
from src.infrastructure.database.repos import MonitorRepository

monitor_router = Router()


@monitor_router.message(F.text == Buttons.START["menu_add_site"])
async def start_add_monitor(message: Message, state: FSMContext):
    """
    Инициация процесса добавления нового монитора.
    Переводит пользователя в состояние ожидания URL.
    """
    await message.answer(text=Texts.MySites.ADD_SITE)
    await state.set_state(MonitorAdd.waiting_for_url)


@monitor_router.message(StateFilter(MonitorAdd.waiting_for_url))
async def process_url(message: Message, state: FSMContext, repo: MonitorRepository):
    """
    Валидация URL и сохранение в базу данных.
    Обрабатывает дубликаты и некорректный ввод.
    """
    raw_url = message.text.strip()

    # Автоматическое добавление схемы, если отсутствует
    if not raw_url.startswith(("http://", "https://")):
        target_url = f"https://{raw_url}"
    else:
        target_url = raw_url

    # Строгая валидация структуры URL
    parsed = urlparse(target_url)
    if not parsed.netloc or "." not in parsed.netloc:
        await message.answer(text=Texts.MySites.INVALID_URL)
        return

    try:
        # Попытка сохранения в БД
        monitor = await repo.add_monitor(
            user_id=message.from_user.id,
            url=target_url,
            interval=300,
        )

        await message.answer(text=Texts.MySites.MONITOR_ADDED.format(monitor.url))
        await state.clear()

    except IntegrityError:
        # Обработка случая, если такой URL уже есть у пользователя
        await message.answer(text=Texts.MySites.ALREADY_ADDED)
        await state.clear()

    except Exception:
        # Логирование ошибки должно происходить в middleware или тут через logger
        await message.answer(text=Texts.MySites.UNEXPECTED_ERROR)
        await state.clear()
