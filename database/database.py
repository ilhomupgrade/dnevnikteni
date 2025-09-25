import sqlite3
from typing import Dict, List, Tuple

DB_PATH = "shadow_work.db"

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_premium INTEGER DEFAULT 0
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS answers (
            user_id INTEGER,
            day INTEGER,
            step INTEGER,
            answer TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, day, step)
        )
        """
    )
    # Миграции для новых колонок (idempotent)
    c.execute("PRAGMA table_info(users)")
    cols = {row[1] for row in c.fetchall()}
    migrations = []
    if "reminders_enabled" not in cols:
        migrations.append("ALTER TABLE users ADD COLUMN reminders_enabled INTEGER DEFAULT 1")
    if "morning_time" not in cols:
        migrations.append("ALTER TABLE users ADD COLUMN morning_time TEXT DEFAULT '08:00'")
    if "evening_time" not in cols:
        migrations.append("ALTER TABLE users ADD COLUMN evening_time TEXT DEFAULT '20:00'")
    if "last_morning" not in cols:
        migrations.append("ALTER TABLE users ADD COLUMN last_morning DATE")
    if "last_evening" not in cols:
        migrations.append("ALTER TABLE users ADD COLUMN last_evening DATE")
    for sql in migrations:
        c.execute(sql)
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Dict[str, bool]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_premium FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        is_premium = 0
    else:
        is_premium = row[0]
    conn.close()
    return {"user_id": user_id, "is_premium": bool(is_premium)}


def set_premium(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def save_answer(user_id: int, day: int, step: int, answer: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO answers (user_id, day, step, answer)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, day, step, answer),
    )
    conn.commit()
    conn.close()


def get_users_for_reminders() -> List[Tuple[int, str, str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, morning_time, evening_time, IFNULL(last_morning,''), IFNULL(last_evening,'')
        FROM users
        WHERE reminders_enabled = 1
        """
    )
    rows = c.fetchall()
    conn.close()
    return rows


def mark_morning_sent(user_id: int, date_str: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_morning=? WHERE user_id=?", (date_str, user_id))
    conn.commit()
    conn.close()


def mark_evening_sent(user_id: int, date_str: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_evening=? WHERE user_id=?", (date_str, user_id))
    conn.commit()
    conn.close()
