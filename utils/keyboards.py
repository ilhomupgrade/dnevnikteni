from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_exercise_keyboard(day_number: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать упражнение", callback_data=f"start_main_{day_number}")],
            [InlineKeyboardButton(text="Вечерняя рефлексия", callback_data=f"start_evening_{day_number}")]
        ]
    )


def get_premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать @ilhom_upgrade", url="https://t.me/ilhom_upgrade")]
        ]
    )
