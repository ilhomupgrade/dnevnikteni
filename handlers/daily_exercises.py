import json
from typing import Optional

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from database.database import get_user, save_answer
from utils.keyboards import get_exercise_keyboard, get_premium_keyboard
from utils.states import ExerciseStates

router = Router()

with open("data/exercises.json", encoding="utf-8") as f:
    EXERCISES_DATA = json.load(f)


def get_day_data(day_number: str) -> Optional[dict]:
    return EXERCISES_DATA["days"].get(day_number)


async def send_day_intro(
    message: types.Message,
    day_number: str,
    state: FSMContext,
    user_id: int,
) -> None:
    day_data = get_day_data(day_number)
    if not day_data:
        await message.answer("Такого дня нет.")
        return

    user = get_user(user_id)
    if not day_data.get("is_free", False) and not user["is_premium"]:
        await message.answer(
            "Доступ к этому дню только для Premium-подписчиков.\n\n"
            "Для продолжения напишите @ilhom_upgrade",
            reply_markup=get_premium_keyboard(),
        )
        return

    if day_data.get("trigger_warning"):
        await message.answer(day_data["trigger_warning"])

    next_day_number = str(int(day_number) + 1)
    if not get_day_data(next_day_number):
        next_day_number = None

    morning_text = day_data.get("morning", {}).get("text", "")
    title = day_data.get("title", "")
    text = f"🌅 День {day_number}: {title}\n\n{morning_text}"

    await message.answer(
        text,
        reply_markup=get_exercise_keyboard(day_number, next_day_number),
    )
    await state.clear()


@router.message(F.text.regexp(r"^/day(\d+)$"))
async def handle_day(message: types.Message, state: FSMContext) -> None:
    day_number = message.text.replace("/day", "")
    await send_day_intro(message, day_number, state, message.from_user.id)


@router.callback_query(F.data.regexp(r"^next_day_(\d+)$"))
async def handle_next_day(callback: types.CallbackQuery, state: FSMContext) -> None:
    day_number = callback.data.replace("next_day_", "")
    await send_day_intro(callback.message, day_number, state, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^start_main_(\d+)$"))
async def start_main_exercise(callback: types.CallbackQuery, state: FSMContext) -> None:
    day_number = callback.data.replace("start_main_", "")
    day_data = get_day_data(day_number)
    user = get_user(callback.from_user.id)

    if not day_data:
        await callback.message.answer("Такого дня нет.")
        await callback.answer()
        return

    if not day_data.get("is_free", False) and not user["is_premium"]:
        await callback.message.answer(
            "Доступ к этому дню только для Premium-подписчиков.",
            reply_markup=get_premium_keyboard(),
        )
        await callback.answer()
        return

    steps = day_data.get("main", {}).get("steps", [])
    if not steps:
        await callback.message.answer("Для этого дня пока нет шагов упражнения.")
        await callback.answer()
        return

    await callback.message.answer(f"Шаг 1: {steps[0]['text']}")
    await state.set_state(ExerciseStates.waiting_main)
    await state.update_data(day_number=day_number, step_index=0)
    await callback.answer()


@router.message(ExerciseStates.waiting_main)
async def process_main_step(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    day_number = data.get("day_number") if data else None
    step_index = data.get("step_index") if data else None

    if day_number is None or step_index is None:
        await message.answer("Пожалуйста, выберите день командой /dayN и начните упражнение заново.")
        await state.clear()
        return

    day_data = get_day_data(day_number)
    if not day_data:
        await message.answer("Не удалось найти данные по выбранному дню. Попробуйте открыть его снова.")
        await state.clear()
        return

    steps = day_data.get("main", {}).get("steps", [])
    if step_index >= len(steps):
        await message.answer("Шаги упражнения завершены. Нажмите 'Вечерняя рефлексия', когда будете готовы.")
        await state.clear()
        return

    save_answer(message.from_user.id, int(day_number), step_index, message.text)

    if step_index + 1 < len(steps):
        next_step = steps[step_index + 1]
        await message.answer(f"Шаг {step_index + 2}: {next_step['text']}")
        await state.update_data(step_index=step_index + 1)
    else:
        await message.answer(
            "Основное упражнение завершено! Нажмите 'Вечерняя рефлексия', когда будете готовы."
        )
        await state.clear()


@router.callback_query(F.data.regexp(r"^start_evening_(\d+)$"))
async def start_evening(callback: types.CallbackQuery, state: FSMContext) -> None:
    day_number = callback.data.replace("start_evening_", "")
    day_data = get_day_data(day_number)
    user = get_user(callback.from_user.id)

    if not day_data:
        await callback.message.answer("Такого дня нет.")
        await callback.answer()
        return

    if not day_data.get("is_free", False) and not user["is_premium"]:
        await callback.message.answer(
            "Доступ к этому дню только для Premium-подписчиков.",
            reply_markup=get_premium_keyboard(),
        )
        await callback.answer()
        return

    evening = day_data.get("evening")
    if not evening:
        await callback.message.answer("Вечерняя рефлексия для этого дня не предусмотрена.")
        await callback.answer()
        return

    await callback.message.answer(f"🌙 Вечерняя рефлексия\n\n{evening['text']}")
    await state.set_state(ExerciseStates.waiting_evening)
    await state.update_data(day_number=day_number)
    await callback.answer()


@router.message(ExerciseStates.waiting_evening)
async def process_evening(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    day_number = data.get("day_number") if data else None

    if not day_number:
        await message.answer("Пожалуйста, откройте нужный день и начните вечернюю практику заново.")
        await state.clear()
        return

    save_answer(message.from_user.id, int(day_number), 99, message.text)

    day_data = get_day_data(day_number) or {}
    if day_number == "7" and day_data.get("is_premium_transition"):
        pm = day_data.get("premium_message", {})
        achievements = "\n".join(f"• {a}" for a in pm.get("achievements", []))
        preview = "\n".join(f"— {item}" for item in pm.get("next_weeks_preview", []))
        contact = pm.get("contact", "")
        text = (
            f"🎉 {pm.get('title', '')}\n\n{achievements}\n\nДальше вас ждёт:\n{preview}\n\nКонтакт: {contact}"
        )
        await message.answer(text, reply_markup=get_premium_keyboard())
    else:
        await message.answer("Спасибо за рефлексию! До завтра.")
    await state.clear()
