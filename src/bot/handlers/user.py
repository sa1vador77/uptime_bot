from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from src.bot.lexicon import Texts
from src.bot.markups.reply import main_menu_kb
from src.infrastructure.database.repos import MonitorRepository


user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, repo: MonitorRepository):
    """
    Обработчик команды /start.
    """
    # Пример использования репозитория (пока просто для теста коннекта)
    user_monitors = await repo.get_user_monitors(user_id=message.from_user.id)

    text = Texts.Start.WELCOME
    if user_monitors:
        text += Texts.Start.FOLLOWED_SITES.format(len(user_monitors))

    await message.answer(
        text=text,
        reply_markup=main_menu_kb(),
    )
