import sqlite3

# Создание и инициализация базы данных
def init_db_meet():
    conn = sqlite3.connect("meet.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meet (
            MeetID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Description TEXT,
            Data INTEGER,
            TimeFrom INTEGER,
            TimeTo INTEGER,
            TeamID INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_meet(name: str, description: str, data, time_from, time_to, team_id) -> int:
    conn = sqlite3.connect("meet.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meet (Name, Description, Data, TimeFrom, TimeTo, TeamID) VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, data, time_from, time_to, team_id))
    meet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meet_id


