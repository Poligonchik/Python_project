import sqlite3
import os

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
            Data INTEGER,
            TimeFrom DATETIME,
            TimeTo DATETIME,
            TeamID INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_meet(name: str, description: str, data, time_from, time_to, team_id) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meet (Name, Description, Data, TimeFrom, TimeTo, TeamID) VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, data, time_from, time_to, team_id))
    meet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meet_id


