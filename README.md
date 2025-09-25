# Дневник внутренней силы — Telegram-бот

## Запуск

1. Установите Python 3.10+
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Укажите токен в `.env` (уже проставлен):
   ```env
   BOT_TOKEN=... ваш токен ...
   ```
4. Запуск:
   ```bash
   python main.py
   ```

## Команды
- /start — приветствие
- /day1, /day2, /day7, /day8 — запуск упражнений (1,2,7 — бесплатно; 8 — premium)

## Файлы
- `data/exercises.json` — контент упражнений
- `database/database.py` — SQLite БД (пользователи, ответы)
- `handlers/` — обработчики бота
- `utils/` — клавиатуры и FSM
