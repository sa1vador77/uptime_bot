from typing import Sequence

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.bot.lexicon import Buttons


def render_reply_kb(*row_sizes: int, buttons: Sequence[str]) -> ReplyKeyboardMarkup:
    """Создаёт Reply-клавиатуру по списку подписей и схеме рядов.

    На основе переданных подписей создаёт кнопки и распределяет их по рядам
    с помощью ReplyKeyboardBuilder.adjust(). Например, схема (2, 1) означает,
    что в первом ряду будет 2 кнопки, во втором — 1, оставшиеся кнопки
    будут автоматически распределены по последнему размеру.

    Args:
        *row_sizes: Размеры рядов (по количеству кнопок в каждом ряду),
            передаются только позиционно.
        buttons: Подписи кнопок в порядке добавления.

    Returns:
        Готовый объект ReplyKeyboardMarkup с включённым resize_keyboard.
    """
    builder = ReplyKeyboardBuilder()

    for text in buttons:
        builder.button(text=text)

    if row_sizes:
        builder.adjust(*row_sizes)

    return builder.as_markup(resize_keyboard=True)


def main_menu_kb() -> ReplyKeyboardMarkup:
    """
    Генерация главной клавиатуры бота.
    """
    
    kb = render_reply_kb(2, 2, buttons=list([value for value in Buttons.START.values()]))

    return kb
