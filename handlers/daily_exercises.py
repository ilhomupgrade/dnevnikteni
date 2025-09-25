from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import json
from database.database import get_user, save_answer
from utils.keyboards import get_exercise_keyboard, get_premium_keyboard
from utils.states import ExerciseStates

router = Router()

with open("data/exercises.json", encoding="utf-8") as f:
    EXERCISES_DATA = json.load(f)


@router.message(F.text.regexp(r"^/day(\d+)$"))
async def handle_day(message: types.Message, state: FSMContext):
    day_number = message.text.replace("/day", "")
    day_data = EXERCISES_DATA["days"].get(day_number)
    if not day_data:
        await message.answer("Такого дня нет.")
        return

    user = get_user(message.from_user.id)
    if not day_data.get("is_free", False) and not user["is_premium"]:
        await message.answer(
            "Доступ к этому дню только для Premium-подписчиков.\n\n"
            "Для продолжения напишите @ilhom_upgrade",
            reply_markup=get_premium_keyboard(),
        )
        return

    if day_data.get("trigger_warning"):
        await message.answer(day_data["trigger_warning"])

    morning = day_data["morning"]
    text = f"🌅 День {day_number}: {day_data['title']}\n\n{morning['text']}"
    await message.answer(text, reply_markup=get_exercise_keyboard(day_number))
    await state.set_state(ExerciseStates.waiting_main)
    await state.update_data(day_number=day_number, step_index=0)


@router.callback_query(F.data.regexp(r"^start_main_(\d+)$"))
async def start_main_exercise(callback: types.CallbackQuery, state: FSMContext):
    day_number = callback.data.replace("start_main_", "")
    day_data = EXERCISES_DATA["days"].get(day_number)
    steps = day_data["main"]["steps"]
    step = steps[0]
    await callback.message.answer(f"Шаг 1: {step['text']}")
    await state.update_data(day_number=day_number, step_index=0)
    await state.set_state(ExerciseStates.waiting_main)
    await callback.answer()


@router.message(ExerciseStates.waiting_main)
async def process_main_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    day_number = data["day_number"]
    step_index = data["step_index"]
    day_data = EXERCISES_DATA["days"][day_number]
    steps = day_data["main"]["steps"]

    save_answer(message.from_user.id, int(day_number), step_index, message.text)

    if step_index + 1 < len(steps):
        next_step = steps[step_index + 1]
        await message.answer(f"Шаг {step_index + 2}: {next_step['text']}")
        await state.update_data(step_index=step_index + 1)
    else:
        await message.answer("Основное упражнение завершено! Нажмите 'Вечерняя рефлексия' когда будете готовы.")
        await state.clear()


@router.callback_query(F.data.regexp(r"^start_evening_(\d+)$"))
async def start_evening(callback: types.CallbackQuery, state: FSMContext):
    day_number = callback.data.replace("start_evening_", "")
    day_data = EXERCISES_DATA["days"].get(day_number)
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
async def process_evening(message: types.Message, state: FSMContext):
    data = await state.get_data()
    day_number = data["day_number"]
    # Сохраним как шаг 99 для отделения от дневных шагов
    save_answer(message.from_user.id, int(day_number), 99, message.text)

    day_data = EXERCISES_DATA["days"].get(day_number)
    if day_number == "7" and day_data.get("is_premium_transition"):
        pm = day_data["premium_message"]
        text = (
            f"🎉 {pm['title']}\n\n" +
            "\n".join(f"• {a}" for a in pm["achievements"]) +
            "\n\nДальше вас ждёт:\n" +
            "\n".join(f"— {n}" for n in pm["next_weeks_preview"]) +
            f"\n\nКонтакт: {pm['contact']}"
        )
        await message.answer(text, reply_markup=get_premium_keyboard())
    else:
        await message.answer("Спасибо за рефлексию! До завтра.")
    await state.clear()
