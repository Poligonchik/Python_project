import sqlite3

# Создание и инициализация базы данных
def init_db_sleep_time():
    conn = sqlite3.connect("sleep_time.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_time (
                UserId INTEGER PRIMARY KEY,
                TimeFrom INTEGER DEFAULT 0,
                TimeTo INTEGER DEFAULT 0
            )
        """)
    conn.commit()
    conn.close()


# Функция для добавления статистики для пользователя
def create_sleep_time(user_id: int):
    conn = sqlite3.connect("sleep_time.db")
    cursor = conn.cursor()
    cursor.execute("""
            INSERT INTO sleep_time (UserId) VALUES (?)
        """, (user_id,))
    conn.commit()
    conn.close()


# Функция для добавления статистики встречи
def edit_sleep_time_from(user_id: int, time_from: int):
    conn = sqlite3.connect("sleep_time.db")
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE sleep_time
            SET TimeFrom = ?
            WHERE UserId = ?
        """, (time_from, user_id))

    conn.commit()
    conn.close()

def edit_sleep_time_to(user_id: int, time_to: int):
    conn = sqlite3.connect("sleep_time.db")
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE sleep_time
            SET TimeTo = ?
            WHERE UserId = ?
        """, (time_to, user_id))

    conn.commit()
    conn.close()

