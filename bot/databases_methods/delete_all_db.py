import sqlite3


def clear_database(db_name: str):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Получить только пользовательские таблицы (исключая системные)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()

    # Удалить каждую пользовательскую таблицу
    for table_name in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")

    conn.commit()
    conn.close()


# Использование: clear_database("users.db")