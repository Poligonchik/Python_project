from telegram import Update
from datetime import datetime, timedelta
from bot.google_calendar.google_calendar import create_event
from bot.databases_methods.db_user import get_user_calendar_id, get_user_id_by_telegram_id
from bot.databases_methods.db_meet import create_meet
from bot.google_calendar.google_calendar import get_credentials
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

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
    creds = get_credentials(user_id)
    calendar_id = get_user_calendar_id(user_id)

    if not creds or not creds.valid:
        await update.message.reply_text("Авторизуйте доступ к вашему Google Календарю.")
        return SET_EVENT_TITLE_MP

    if not calendar_id:
        await update.message.reply_text("Не найден Calendar ID. Отправьте идентификатор календаря")
        return SET_EVENT_TITLE_MP

    # Сохраняем UserId инициатора и Calendar ID в user_data
    context.user_data['user_id'] = user_id
    context.user_data['calendar_id'] = calendar_id

    await update.message.reply_text("Введите название встречи:")
    return SET_EVENT_TITLE_MP


async def set_event_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    participants = update.message.text.strip().split(",")  # Разделяем email через запятую
    participants = [email.strip() for email in participants if email.strip()]  # Убираем лишние пробелы и пустые строки
    context.user_data['participants'] = participants  # Сохраняем список email

    if not participants:
        await update.message.reply_text(
            "Вы не ввели ни одного участника. Если хотите добавить участников, введите их email через запятую")

    await update.message.reply_text(
        "Введите дату и время начала встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-31 17:45):")
    return SET_EVENT_START_MP

# Выбираем название события
async def set_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data['event_title'] = title  # Сохраняем название события
    await update.message.reply_text("Введите описание встречи:")
    return SET_EVENT_DESCRIPTION_MP


# Выбираем описание события
async def set_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text.strip()
    context.user_data['event_description'] = description  # Сохраняем описание события
    await update.message.reply_text("Введите email участников встречи через запятую (например, email1@example.com, email2@example.com):")
    return SET_EVENT_PARTICIPANTS_MP


# Установка времени начала встречи
async def set_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time_str = update.message.text.strip()
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        context.user_data['event_start_time'] = start_time
        await update.message.reply_text("Введите дату и время окончания встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-31 18:45):")
        return SET_EVENT_END_MP
    except ValueError:
        await update.message.reply_text("Некорректный формат времени. Попробуйте еще раз.")
        return SET_EVENT_START_MP

async def set_event_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    end_time_str = update.message.text.strip()
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)

    try:
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
        start_time = context.user_data['event_start_time']
        if end_time <= start_time:
            await update.message.reply_text("Время окончания должно быть позже времени начала. Попробуйте ещё раз.")
            return SET_EVENT_END_MP

        creds = get_credentials(user_id)
        calendar_id = context.user_data['calendar_id']
        title = context.user_data['event_title']
        description = context.user_data['event_description']
        participants = context.user_data.get('participants', [])

        # Создаём событие с участниками
        event = create_event(
            creds,
            calendar_id,
            summary=title,
            description=description,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            attendees_emails=participants if participants else None
        )
        await update.message.reply_text(f"Событие успешно создано: {event.get('htmlLink')}")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный формат времени. Попробуйте ещё раз.")
        return SET_EVENT_END_MP
    except Exception as e:
        await update.message.reply_text(f"Ошибка при создании события: {e}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен.")
    return ConversationHandler.END


def get_meeting_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("create_meeting", start_meeting)],  # Здесь начинается диалог
        states={
            SET_EVENT_TITLE_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_title)],
            SET_EVENT_DESCRIPTION_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_description)],
            SET_EVENT_PARTICIPANTS_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_participants)],
            SET_EVENT_START_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_start)],
            SET_EVENT_END_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_end)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

