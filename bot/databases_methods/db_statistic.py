import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "statistic.db")

# Создание и инициализация базы данных
def init_db_statistic():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statistic (
            UserId INTEGER PRIMARY KEY,
            AllTime INTEGER DEFAULT 0,
            CountOfMeets INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления статистики для пользователя
def create_statistic(user_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO statistic (UserId) VALUES (?)
    """, (user_id,))
    conn.commit()
    conn.close()

# Функция для добавления статистики встречи
def add_time_to_alltime(user_id: int, additional_time: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE statistic
        SET AllTime = AllTime + ?
        WHERE UserId = ?
    """, (additional_time, user_id))

    cursor.execute("""
        UPDATE statistic
        SET CountOfMeets = CountOfMeets + 1
        WHERE UserId = ?
    """, (user_id, ))

    conn.commit()
    conn.close()
