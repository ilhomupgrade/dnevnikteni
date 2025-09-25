import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, daily_exercises
from database.database import init_db
from services.notification_service import reminders_loop


async def main() -> None:
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(
        start.router,
        daily_exercises.router,
    )

    # Запускаем фоновые напоминания
    asyncio.create_task(reminders_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
