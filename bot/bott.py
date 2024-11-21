from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    await update.message.reply_text(f'Привет, {user_name}! Рад тебя видеть!')

def main():
    # Вставьте свой токен Telegram API сюда
    TOKEN = "7594370282:AAGpyh78Cr9TXqWyxYlBBJDv_BN34V2e5Jw"

    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Запускаем бота
    application.run_polling()

    #ПРИВЕЕЕЕЕТ

if __name__ == "__main__":
    main()
