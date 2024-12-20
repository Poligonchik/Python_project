from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from datetime import datetime

from bot.databases_methods.db_user import edit_user_name, get_user_by_link, get_link_by_user_id
from bot.databases_methods.db_sleep_time import edit_sleep_time_to, edit_sleep_time_from, get_sleep_time
from bot.databases_methods.db_black_list import create_block
from bot.google_calendar.handlers_calendar import handle_calendar_url
# Этапы диалога
from bot.constants import CHOICE

CHOICE, EDIT_NAME, EDIT_TIME_FROM, EDIT_TIME_TO, BLOCK_USER = range(5)
# Команда /edit
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    curr_user = get_user_by_link(user.username)

    row = get_sleep_time(curr_user[0])
    t_from = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')  # Конвертация строки в дату и время
    t_to = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
    mail = get_link_by_user_id(user.username)
    if mail == "":
        mail = "Почта не привязана к аккаунту"

    await update.message.reply_text(
        f'''Ваши данные:
    1. Имя пользователя {curr_user[1]}
    2. ТГ id @{user.username}
    3. Время сна {t_from.strftime('%H:%M')} - {t_to.strftime('%H:%M')}
    4. Почта, к которой привязан календарь: {mail}
    
Выберите действие:
    /edit_name - Сменить имя
    /edit_sleep_time - Изменить время сна 
    /block_user - Добавить пользователя в черный список
    /cancel - отмена''')
    return ConversationHandler.END
#/edit_calendar - Привязать другой календарь
# Замена имени
async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте новое имя:")
    return EDIT_NAME

async def handle_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_name = update.message.text
    user = update.message.from_user

    edit_user_name(user.username, new_name)
    await update.message.reply_text(f"Имя успешно изменено на {new_name}!")
    return ConversationHandler.END

# Изменение времени сна
async def edit_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Пожалуйста, отправьте новое время начала сна в формате ЧЧ:ММ (например, 22:30):"
    )
    return EDIT_TIME_FROM


async def edit_sleep_time_prompt2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_time_from = update.message.text.strip()

    user = update.message.from_user
    user_id = get_user_by_link(user.username)[0]

    try:
        # Парсим время в формате ЧЧ:ММ и фиксируем дату для time_from
        time_from = datetime.strptime(new_time_from, "%H:%M")
        time_from = time_from.replace(year=1999, month=1, day=1)
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат времени. Убедитесь, что время указано в формате ЧЧ:ММ (например, 22:30)."
        )
        return EDIT_TIME_FROM

    # Сохраняем в базу данных
    edit_sleep_time_from(user_id, time_from)
    await update.message.reply_text(
        "Пожалуйста, отправьте новое время окончания сна в формате ЧЧ:ММ (например, 09:30):"
    )
    return EDIT_TIME_TO

async def handle_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_time_to = update.message.text.strip()

    user = update.message.from_user
    user_id = get_user_by_link(user.username)[0]

    try:
        time_to = datetime.strptime(new_time_to, "%H:%M")
        time_to = time_to.replace(year=1999, month=1, day=1)
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат времени. Убедитесь, что время указано в формате ЧЧ:ММ (например, 09:30)."
        )
        return EDIT_TIME_TO
    edit_sleep_time_to(user_id, time_to)
    row = get_sleep_time(user_id)
    t_from = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
    t_to = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
    if t_from > t_to:
        t_to = t_to.replace(year=1999, month=1, day=2)

    edit_sleep_time_to(user_id, t_to)

    await update.message.reply_text(
        f"Время сна успешно изменено: с {t_from.strftime('%H:%M')} до {t_to.strftime('%H:%M')}."
    )
    return ConversationHandler.END

# Добавление в черный список
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте ник пользователя(@user) в формате user, без @")
    return BLOCK_USER

async def handle_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    blocked_user = update.message.text
    user_id = update.effective_user.id

    if not create_block(user_id, blocked_user):
        await update.message.reply_text("Пользователь не найден. Отправьте ник пользователя бота в телеграмме(@user) в формате user, то есть без @.\nИли /cancel - отмена дейстивия")
        return BLOCK_USER

    await update.message.reply_text(f"Вы успешно заблокировали пользователя {blocked_user}!")
    return ConversationHandler.END

async def edit_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пришлите идентификатор календаря. "
            f"Для главного календаря это ваша почта, а для остальных перейдите в настройки календаря -> "
            f"Интеграция календаря -> Идентификатор календаря")
    return CHOICE
# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. До встречи!")
    return ConversationHandler.END

# ConversationHandler для /edit
def get_edit_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("edit", edit),
                      CommandHandler("edit_name", edit_name),
                      CommandHandler("edit_sleep_time", edit_sleep_time),
                      CommandHandler("edit_calendar", edit_calendar),
                      CommandHandler("block_user", block_user),
                     ],
        states={
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_name)],
            EDIT_TIME_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_sleep_time_prompt2)],
            EDIT_TIME_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sleep_time)],
            BLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
