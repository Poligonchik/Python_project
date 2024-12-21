import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "black_list.db")

DATABASE_DIR2 = os.path.join(BASE_DIR, "../databases")
db_path2 = os.path.join(DATABASE_DIR2, "users.db")

# Создание и инициализация базы данных
def init_db_black_list():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS black_list (
            UserId INTEGER NOT NULL,
            BlockedUserId INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Функция для добавления блокировки
def create_block(user_id: int, blocked_user_link: str):
    conn = sqlite3.connect(db_path2)
    cursor = conn.cursor()

    cursor.execute(f"ATTACH DATABASE '{db_path2}' AS users_db")

    cursor.execute("""
        SELECT UserId
        FROM users_db.users
        WHERE TelegramLink = ?
    """, (blocked_user_link,))

    result = cursor.fetchone()

    if result is None:
        return False


    blocked_user_id = result[0]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO black_list (UserId, BlockedUserId) VALUES (?, ?)
    """, (user_id, blocked_user_id))

    conn.commit()
    conn.close()
    return True
