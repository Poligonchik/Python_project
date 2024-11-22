from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from bot.databases.db_user import edit_user_name, get_user_by_link
from bot.databases.db_sleep_time import edit_sleep_time_to, edit_sleep_time_from
from bot.databases.db_black_list import create_block

# Этапы диалога
CHOICE_EDIT_DATA, EDIT_NAME, EDIT_TIME_FROM, EDIT_TIME_TO, BLOCK_USER = range(5)

# Команда /edit
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        ["Сменить имя", "Изменить время сна", "Изменить Гугл Календарь", "Добавить пользователя в черный список"],
    ]
    user = update.message.from_user
    curr_user = get_user_by_link(user.username)

    await update.message.reply_text(
        f'''Ваши данные:
    1. Имя пользователя {curr_user[1]}
    2. ТГ id @{user.username}
    3. Время сна -
    4. Гугл календарь -
Выберите данные, которые хотите изменить:''',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOICE_EDIT_DATA

# Замена имени
async def edit_user_name_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте новое имя:")
    return EDIT_NAME

async def handle_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_name = update.message.text
    user = update.message.from_user

    edit_user_name(user.username, new_name)
    await update.message.reply_text(f"Имя успешно изменено на {new_name}!")
    return ConversationHandler.END

# Изменение времени сна
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

# Добавление в черный список
async def add_user_to_black_list_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте ник пользователя(@user) в формате user, без @")
    return BLOCK_USER

async def handle_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    blocked_user = update.message.text
    user_id = update.effective_user.id

    create_block(user_id, blocked_user)
    await update.message.reply_text(f"Вы успешно заблокировали пользователя {blocked_user}!")
    return ConversationHandler.END

# Выбор действия в меню редактирования
async def choice_edit_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Сменить имя":
        return await edit_user_name_prompt(update, context)

    elif update.message.text == "Изменить время сна":
        return await edit_sleep_time_prompt(update, context)

    elif update.message.text == "Изменить Гугл Календарь":
        pass

    elif update.message.text == "Добавить пользователя в черный список":
        return await add_user_to_black_list_prompt(update, context)

    else:
        await update.message.reply_text("Пожалуйста, выберите из предложенных вариантов.")
        return CHOICE_EDIT_DATA

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. До встречи!")
    return ConversationHandler.END

# ConversationHandler для /edit
def get_edit_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("edit", edit)],
        states={
            CHOICE_EDIT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice_edit_data)],
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_name)],
            EDIT_TIME_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_sleep_time_prompt2)],
            EDIT_TIME_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sleep_time)],
            BLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
