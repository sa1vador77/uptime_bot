from aiogram.fsm.state import StatesGroup, State


class MonitorAdd(StatesGroup):
    waiting_for_url = State()
