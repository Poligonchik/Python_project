import sqlite3

# Создание и инициализация базы данных
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

# Функция для добавления пользователя
def add_user(name: str, telegram_link: str, google_calendar_link: str) -> int:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (Name, TelegramLink, GoogleCalendarLink) VALUES (?, ?, ?)
    """, (name, telegram_link, google_calendar_link))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

# Проверка, есть ли пользователь в базе
def get_user_by_link(telegram_link: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE TelegramLink = ?
    """, (telegram_link,))
    user = cursor.fetchone()
    conn.close()
    return user