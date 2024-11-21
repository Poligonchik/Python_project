from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# Этапы диалога ПРИМЕР
START, CHOICE, MEETING_OPTION, SET_TIME = range(4)

# Команда /start
# Начало диалога
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Изменить данные пользователя", "Добавить встречу", "Статистика"]]

    await update.message.reply_text(
        "Привет, я телеграмм бот консьерж! Что вы хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOICE

# Выбор действия
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Изменить данные пользователя":
        await update.message.reply_text("Вы выбрали изменить данные. Пока это действие не реализовано.")
        return ConversationHandler.END
    elif update.message.text == "Добавить встречу":
        #ВЫБОР НАЗВАНИЯ, ПОЛЬЗОВАТЕЛЕЙ
        reply_keyboard = [["Автоустановка времени", "Ввести время вручную"]]
        await update.message.reply_text(
            "Как вы хотите установить время встречи?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return MEETING_OPTION
    elif update.message.text == "Статистика":
        await update.message.reply_text("Вы выбрали просмотр статистики. Пока это действие не реализовано.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов.")
        return CHOICE

# Выбор метода добавления встречи
async def meeting_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Автоустановка времени":
        #Надо реализовать
        await update.message.reply_text("Встреча назначена автоматически на завтра в 10:00.")
        return ConversationHandler.END
    elif update.message.text == "Ввести время вручную":
        await update.message.reply_text("Введите время встречи в формате ЧЧ:ММ (например, 14:30):")
        return SET_TIME
    else:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов.")
        return MEETING_OPTION

# Установка времени вручную
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_time = update.message.text
    await update.message.reply_text(f"Встреча назначена на {user_time}. Спасибо!")
    return ConversationHandler.END

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. До встречи!")
    return ConversationHandler.END

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Список команд:\n/start - начать\n/help - помощь\n")

# Основная функция
if __name__ == "__main__":
    app = ApplicationBuilder().token("7594370282:AAGpyh78Cr9TXqWyxYlBBJDv_BN34V2e5Jw").build()

    app.add_handler(CommandHandler("help", help))

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            MEETING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, meeting_option)],
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен!")
    app.run_polling()
