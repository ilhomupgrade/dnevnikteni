import asyncio
from datetime import datetime, date
from aiogram import Bot
from database.database import get_users_for_reminders, mark_morning_sent, mark_evening_sent


async def reminders_loop(bot: Bot) -> None:
    while True:
        now = datetime.now()
        today_str = date.today().isoformat()
        for user_id, m_time, e_time, last_m, last_e in get_users_for_reminders():
            if now.strftime('%H:%M') == m_time and last_m != today_str:
                try:
                    await bot.send_message(user_id, "🌅 Напоминание: время для утренней практики. Напишите /day1 или текущий день.")
                    mark_morning_sent(user_id, today_str)
                except Exception:
                    pass
            if now.strftime('%H:%M') == e_time and last_e != today_str:
                try:
                    await bot.send_message(user_id, "🌙 Напоминание: вечерняя рефлексия ждёт вас.")
                    mark_evening_sent(user_id, today_str)
                except Exception:
                    pass
        await asyncio.sleep(55)
