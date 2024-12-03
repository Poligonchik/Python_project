import sqlite3
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация базы данных пользователей
def init_db_user():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            UserId INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            TelegramLink TEXT NOT NULL,
            GoogleCalendarLink TEXT
        )
    """)
    conn.commit()
    conn.close()

# Добавление нового пользователя
def add_user(name: str, telegram_link: str, google_calendar_link: str) -> int:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (Name, TelegramLink, GoogleCalendarLink) VALUES (?, ?, ?)
    """, (name, telegram_link, google_calendar_link))
    user_id = cursor.lastrowid  # Получаем ID только что добавленного пользователя
    conn.commit()
    conn.close()
    return user_id

# Получение пользователя по TelegramLink
def get_user_by_link(telegram_link: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE TelegramLink = ?
    """, (telegram_link,))
    user = cursor.fetchone()
    conn.close()
    return user

# Изменение имени пользователя
def edit_user_name(tg_link: str, new_name: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET Name = ?
        WHERE TelegramLink = ?
    """, (new_name, tg_link))
    conn.commit()
    conn.close()

# Обновление GoogleCalendarLink пользователя
def edit_user_calendar_id(user_id: int, calendar_id: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET GoogleCalendarLink = ?
        WHERE UserId = ?
    """, (calendar_id, user_id))
    conn.commit()
    conn.close()
    logger.info(f"GoogleCalendarLink обновлён для пользователя {user_id}: {calendar_id}")

# Получение GoogleCalendarLink по UserId
def get_user_calendar_id(user_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT GoogleCalendarLink FROM users WHERE UserId = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    logger.info(f"Извлечён GoogleCalendarLink для пользователя {user_id}: {result[0] if result else None}")
    return result[0] if result else None



# Экспортируем функции
__all__ = [
    "init_db_user",
    "add_user",
    "get_user_by_link",
    "edit_user_name",
    "edit_user_calendar_id",
    "get_user_calendar_id",
]
