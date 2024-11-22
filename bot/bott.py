from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from bot.databases.db_user import init_db_user, add_user, get_user_by_link, edit_user_name
from bot.databases.db_meet import init_db_meet, create_meet
from bot.databases.db_team import init_db_team, create_team
from bot.databases.db_statistic import init_db_statistic, create_statistic, add_time_to_alltime
from bot.databases.db_sleep_time import init_db_sleep_time, create_sleep_time, edit_sleep_time_to, edit_sleep_time_from
from bot.databases.db_black_list import init_db_black_list, create_block

# Этапы диалога
START, CHOICE, CHOICE_EDIT_DATA, EDIT_NAME, EDIT_TIME_FROM, EDIT_TIME_TO, BLOCK_USER, MEETING_OPTION, SET_TIME = range(9)

# Команда /start
# Начало диалога
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    telegram_link = user.username if user.username else user.id

    #Проверка зарегистрирован ли пользователь
    curr_user = get_user_by_link(telegram_link)
    if curr_user:
        await update.message.reply_text(f"Привет, {curr_user[1]}! Рады снова вас видеть!")
    else:
        await update.message.reply_text(f"Здравствуйте, {user.full_name}, чтобы использовать бота, пришлите ссылку на Ваш google календарь.")

        google_calendar_link = "Пока не реализовано"
        user_id = add_user(user.full_name, telegram_link, google_calendar_link)
        create_statistic(user_id)
        create_sleep_time(user_id)
        await update.message.reply_text(f"Отлично, теперь Вы зарегистрированы с ID {user_id}.")

    reply_keyboard = [["Изменить данные пользователя", "Добавить встречу", "Статистика"]]

    await update.message.reply_text(
        "Что вы хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOICE

# Выбор действия
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Изменить данные пользователя":
        reply_keyboard = [["Сменить имя", "Изменить Гугл Календарь", "Изменить время сна", "Добавить пользователя в черный список"]]
        user = update.message.from_user
        await update.message.reply_text(
            f"Вы выбрали изменить данные. Ваши данные:\n Имя пользователя {user.full_name}\n ТГ id {user.username}\n Время сна\n Гугл календарь \nКакие данные вы хотите изменить?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOICE_EDIT_DATA

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

# Замена данных в профиле вспомогательные функция замены имени
async def edit_user_name_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте новое имя:")
    return EDIT_NAME


async def handle_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_name = update.message.text
    user_id = update.effective_user.id

    edit_user_name(user_id, new_name)

    await update.message.reply_text(f"Имя успешно изменено на {new_name}!")
    return ConversationHandler.END

# Замена данных в профиле вспомогательные функция замены времени сна
async def edit_sleep_time_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте новое время начала сна в формате ЧЧ:ММ (например, 22:30):")
    return EDIT_TIME_FROM

async def edit_sleep_time_prompt2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_time_from = update.message.text
    user_id = update.effective_user.id

    edit_sleep_time_from(user_id, int(new_time_from))

    await update.message.reply_text("Пожалуйста, отправьте новое время окончания сна в формате ЧЧ:ММ (например, 9:30):")
    return EDIT_TIME_TO

async def handle_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_time_to = update.message.text
    user_id = update.effective_user.id

    edit_sleep_time_to(user_id, int(new_time_to))

    await update.message.reply_text(f"Время сна успешно изменено.")
    return ConversationHandler.END

# Замена данных в профиле вспомогательные функция замены имени
async def add_user_to_black_list_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте ник пользователя(@user) в формате user, без @")
    return BLOCK_USER


async def handle_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    blocked_user = update.message.text
    user_id = update.effective_user.id

    create_block(user_id, blocked_user)

    await update.message.reply_text(f"Вы успешно заблокировали пользователя {blocked_user}!")
    return ConversationHandler.END

# Замена данных в профиле основная функция
async def choice_edit_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Сменить имя":
        return await edit_user_name_prompt(update, context)

    elif update.message.text == "Изменить Гугл Календарь":
        pass

    elif update.message.text == "Изменить время сна":
        return await edit_sleep_time_prompt(update, context)

    elif update.message.text == "Добавить пользователя в черный список":
        return await add_user_to_black_list_prompt(update, context)

    else:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов.")
        return CHOICE_EDIT_DATA

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
    init_db_user()
    init_db_meet()
    init_db_team()
    init_db_statistic()
    init_db_sleep_time()
    init_db_black_list()
    app = ApplicationBuilder().token("7594370282:AAGpyh78Cr9TXqWyxYlBBJDv_BN34V2e5Jw").build()

    app.add_handler(CommandHandler("help", help))

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            CHOICE_EDIT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice_edit_data)],
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_name)],
            EDIT_TIME_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_sleep_time_prompt2)],
            EDIT_TIME_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sleep_time)],
            BLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block)],
            MEETING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, meeting_option)],
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен!")
    app.run_polling()

