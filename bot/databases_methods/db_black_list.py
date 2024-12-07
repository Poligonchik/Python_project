import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "../databases")
db_path = os.path.join(DATABASE_DIR, "black_list.db")

# Создание и инициализация базы данных
def init_db_black_list():
    conn = sqlite3.connect(db_path)
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
def create_block(user_id: int, blocked_user_link: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("ATTACH DATABASE 'users.db' AS users_db")

    cursor.execute("""
        SELECT UserId
        FROM users_db.users
        WHERE TelegramLink = ?
    """, (blocked_user_link,))

    blocked_user_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO black_list (UserId, BlockedUserId) VALUES (?, ?)
    """, (user_id, blocked_user_id))
    conn.commit()
    conn.close()

