from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Это Дневник внутренней силы. Готовы начать 30-дневное путешествие к себе?\n\n"
        "Чтобы начать, напишите /day1"
    )
