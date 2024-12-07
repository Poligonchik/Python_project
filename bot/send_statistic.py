import sqlite3
import os
from telegram import Update
from bot.databases_methods.db_user import get_user_id_by_telegram_id
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "databases")
db_path = os.path.join(DATABASE_DIR, "statistic.db")

async def get_statistic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_username = update.message.from_user.username

    try:
        user_id = get_user_id_by_telegram_id(telegram_username)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT CountOfMeets, AllTime FROM statistic WHERE UserId = ?
        """, (user_id,))
        result = cursor.fetchone()

        conn.close()

        if result is None:
            await update.message.reply_text("Для вас пока нет записей о встречах. Создайте свою первую встречу!")
            return ConversationHandler.END

        count_of_meets = result[0]
        hours_of_meets = result[1] // 60
        minutes_of_meets = result[1] % 60

        await update.message.reply_text(f"За всё время вы провели {count_of_meets} встреч(и), и в сумме на них вы потратили {hours_of_meets} часов и {minutes_of_meets} минут.")
        return ConversationHandler.END

    except Exception as e:
        # Обрабатываем ошибки и уведомляем пользователя
        await update.message.reply_text(f"Ошибка при получении статистики: {e}")
        return ConversationHandler.END