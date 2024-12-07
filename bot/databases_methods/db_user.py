import sqlite3
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "users.db")


# Инициализация базы данных пользователей
def init_db_user():
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE TelegramLink = ?
    """, (telegram_link,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_link_by_user_id(tg_id: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT GoogleCalendarLink FROM users WHERE TelegramLink = ?
    """, (tg_id,))
    link_g = cursor.fetchone()[0]
    conn.close()
    return link_g

# Изменение имени пользователя
def edit_user_name(tg_link: str, new_name: str):
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT GoogleCalendarLink FROM users WHERE UserId = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    logger.info(f"Извлечён GoogleCalendarLink для пользователя {user_id}: {result[0] if result else None}")
    return result[0] if result else None

def get_user_id_by_telegram_id(telegram_link: str) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT UserId FROM users WHERE TelegramLink = ?
        """, (telegram_link,))
        result = cursor.fetchone()
        if result:
            return result[0]  # Возвращаем UserId
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении UserId: {e}")
        return None
    finally:
        conn.close()



# без этого не работало
__all__ = [
    "init_db_user",
    "add_user",
    "get_user_by_link",
    "edit_user_name",
    "edit_user_calendar_id",
    "get_user_calendar_id",
]
