from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Список доступных команд:\n"
        "/start - Начало работы\n"
        "/help - Список команд\n"
        "/edit - Редактирование данных пользователя\n"
        "/meets - Управление встречами\n"
        "/statistic - Статистика пользователя\n"
    )
    await update.message.reply_text(help_text)

def help_command():
    return CommandHandler("help", help_handler)
