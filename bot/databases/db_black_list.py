import sqlite3

# Создание и инициализация базы данных
def init_db_black_list():
    conn = sqlite3.connect("black_list.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS black_list (
            UserId INTEGER PRIMARY KEY,
            BlockedUserId INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_block(user_id: int, blocked_user_id: int):
    conn = sqlite3.connect("black_list.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO black_list (UserId, BlockedUserId) VALUES (?, ?)
    """, (user_id, blocked_user_id))
    conn.commit()
    conn.close()

