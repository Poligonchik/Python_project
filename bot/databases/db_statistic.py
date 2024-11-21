import sqlite3

# Создание и инициализация базы данных
def init_db_statistic():
    conn = sqlite3.connect("statistic.db")
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
def create_statistic(user_id: int) -> int:
    conn = sqlite3.connect("statistic.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO statistic (UserId) VALUES (?)
    """, (user_id,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

# Функция для добавления статистики встречи
def add_time_to_alltime(user_id: int, additional_time: int):
    conn = sqlite3.connect("statistic.db")
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
