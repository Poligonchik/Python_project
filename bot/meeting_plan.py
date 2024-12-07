from telegram import Update
from datetime import datetime, timedelta
from bot.google_calendar.google_calendar import create_event
from bot.databases_methods.db_user import get_user_id_by_telegram_id, get_user_by_link
from telegram import ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы диалога
(SET_EVENT_TITLE_MP, SET_EVENT_DESCRIPTION_MP,
 SET_EVENT_PARTICIPANTS_MP, SET_EVENT_START_MP, SET_EVENT_END_MP) = range(10, 15)

async def start_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Логика для начала создания встречи
    await update.message.reply_text("Введите название встречи:")
    return SET_EVENT_TITLE_MP

# Команда для создания встречи
async def create_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)  # Получаем UserId из базы

    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе данных.")
        return ConversationHandler.END

    await update.message.reply_text("Введите название встречи:")
    return SET_EVENT_TITLE_MP

async def set_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data['event_title'] = title  # Сохраняем название события
    await update.message.reply_text("Введите описание встречи:")
    return SET_EVENT_DESCRIPTION_MP

async def set_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text.strip()
    context.user_data['event_description'] = description  # Сохраняем описание события
    await update.message.reply_text("Введите email участников встречи через запятую (например, email1@example.com, email2@example.com):")
    return SET_EVENT_PARTICIPANTS_MP

async def set_event_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    participants = update.message.text.strip().split(",")  # Разделяем email через запятую
    participants = [email.strip() for email in participants if email.strip()]  # Убираем лишние пробелы и пустые строки
    context.user_data['participants'] = participants  # Сохраняем список email

    if not participants:
        await update.message.reply_text(
            "Вы не ввели ни одного участника. Если хотите добавить участников, введите их email через запятую."
        )
        return SET_EVENT_PARTICIPANTS_MP

    await update.message.reply_text(
        "Введите дату и время начала встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-31 17:45):"
    )
    return SET_EVENT_START_MP

async def set_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time_str = update.message.text.strip()
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        context.user_data['event_start_time'] = start_time
        await update.message.reply_text(
            "Введите дату и время окончания встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-31 18:45):"
        )
        return SET_EVENT_END_MP
    except ValueError:
        await update.message.reply_text("Некорректный формат времени. Попробуйте еще раз.")
        return SET_EVENT_START_MP

async def set_event_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    end_time_str = update.message.text.strip()
    try:
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
        start_time = context.user_data['event_start_time']
        if end_time <= start_time:
            await update.message.reply_text("Время окончания должно быть позже времени начала. Попробуйте ещё раз.")
            return SET_EVENT_END_MP

        context.user_data['event_end_time'] = end_time
        await handle_create_event(update, context)
    except ValueError:
        await update.message.reply_text("Некорректный формат времени. Попробуйте ещё раз.")
        return SET_EVENT_END_MP

async def handle_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = context.user_data.get('event_title')
    description = context.user_data.get('event_description')
    start_time = context.user_data.get('event_start_time')
    end_time = context.user_data.get('event_end_time')
    participants = context.user_data.get('participants', [])

    user_id = get_user_id_by_telegram_id(update.message.from_user.username)
    if user_id:
        user = get_user_by_link(update.message.from_user.username)
        creator_email = user[3]
    if creator_email not in participants:
        participants.append(creator_email)

    # Форматируем время в ISO формат
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    successful_additions = []
    failed_additions = []

    for email in participants:
        success, message = create_event(
            user_email=email,
            summary=summary,
            description=description,
            start_time=start_time_iso,
            end_time=end_time_iso
        )
        if success:
            successful_additions.append(email)
        else:
            failed_additions.append(f"{email}: {message}")

    response_message = "Встреча создана для следующих пользователей:\n"
    if successful_additions:
        response_message += "\n".join(successful_additions)

    if failed_additions:
        response_message += "\n\nНе удалось создать встречу для следующих пользователей:\n"
        response_message += "\n".join(failed_additions)

    await update.message.reply_text(response_message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_meeting_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("create_meeting", create_meeting)],  # Здесь начинается диалог
        states={
            SET_EVENT_TITLE_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_title)],
            SET_EVENT_DESCRIPTION_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_description)],
            SET_EVENT_PARTICIPANTS_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_participants)],
            SET_EVENT_START_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_start)],
            SET_EVENT_END_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_end)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
