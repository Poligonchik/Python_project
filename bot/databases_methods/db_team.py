import sqlite3

# Создание и инициализация базы данных
def init_db_team():
    conn = sqlite3.connect("team.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team (
            TeamID INTEGER PRIMARY KEY,
            UserID INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_team(team_id: int, user_id: int):
    conn = sqlite3.connect("team.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO black_list (TeamID, UserId) VALUES (?, ?)
    """, (team_id, user_id))
    conn.commit()
    conn.close()

