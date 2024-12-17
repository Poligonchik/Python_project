import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "meet.db")

# Создание и инициализация базы данных
def init_db_meet():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meet (
            MeetID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Description TEXT,
            TimeFrom DATETIME,
            TimeTo DATETIME
        )
    """)
    conn.commit()
    conn.close()


# Функция для добавления блокировки
def create_meet(name: str, description: str, time_from: datetime, time_to: datetime) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meet (Name, Description, TimeFrom, TimeTo) VALUES (?, ?, ?, ?)
    """, (name, description, time_from, time_to))
    meet_id = cursor.lastrowid
    conn.commit()
    conn.close()

    meet_id = cursor.lastrowid
    return meet_id


