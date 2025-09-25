from aiogram.fsm.state import StatesGroup, State


class ExerciseStates(StatesGroup):
    waiting_main = State()
    waiting_evening = State()
