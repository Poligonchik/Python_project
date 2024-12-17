import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "team.db")

# Создание и инициализация базы данных
def init_db_team():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team (
            MeetID INTEGER NOT NULL,
            Mail TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_team(meet_id: int, mail: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO black_list (MeetID, Mail) VALUES (?, ?)
    """, (meet_id, mail))
    conn.commit()
    conn.close()

