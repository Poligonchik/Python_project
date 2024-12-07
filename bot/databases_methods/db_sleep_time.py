import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "sleep_time.db")

# Создание и инициализация базы данных
def init_db_sleep_time():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sleep_time (
            UserId INTEGER PRIMARY KEY,
            TimeFrom DATETIME DEFAULT '1999-01-01 00:00:00',
            TimeTo DATETIME DEFAULT '1999-01-01 00:00:00'
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления статистики для пользователя
def create_sleep_time(user_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
            INSERT INTO sleep_time (UserId) VALUES (?)
        """, (user_id,))
    conn.commit()
    conn.close()


# Функция для добавления статистики встречи
def edit_sleep_time_from(user_id: int, time_from: datetime):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE sleep_time
            SET TimeFrom = ?
            WHERE UserId = ?
        """, (time_from.strftime("%Y-%m-%d %H:%M:%S"), user_id))

    conn.commit()
    conn.close()

def edit_sleep_time_to(user_id: int, time_to: datetime):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE sleep_time
            SET TimeTo = ?
            WHERE UserId = ?
        """, (time_to.strftime("%Y-%m-%d %H:%M:%S"), user_id))

    conn.commit()
    conn.close()


def get_sleep_time(user_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
                SELECT * FROM sleep_time WHERE UserId = ?
            """, (user_id,))

    row = cursor.fetchall()

    # Проверка на пустой результат
    if not row:
        conn.close()
        return None  # Возвращаем None, если пользователь не найден

    conn.commit()
    conn.close()

    return row[0]