import re
from telegram import (Update, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters, CallbackContext, MessageHandler, ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from bot.google_calendar.google_calendar import get_credentials, build, delete_event
from bot.databases_methods.db_user import get_email_by_user, get_user_by_email
from datetime import datetime
from googleapiclient.discovery import build

DELETE_MEET = range(1)

async def meets(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text('''Выберите действие:
    /create_meeting - создание новой встречи
    /get_meets - просмотр ожидаемых событий
    /edit_meet - редактировать встречу (не сделано)
    /delete_meet - удалить встречу''')
    return ConversationHandler.END


async def get_meets(update: Update, context: CallbackContext):
    user = update.message.from_user

    user_email = get_email_by_user(user.username)
    res = []
    user = get_user_by_email(user_email)
    if not user:
        await update.message.reply_text(f"Пользователь с email {user_email} не найден в базе данных.")
        return ConversationHandler.END

    user_id = user[0]
    calendar_id = user[3]  # GoogleCalendarLink

    if not calendar_id:
        await update.message.reply_text(f"Вы не привязали календарь, сначала привяжите его. \start")
        return ConversationHandler.END

    creds = get_credentials(user_id)

    service = build('calendar', 'v3', credentials=creds)

    # Получаем текущее время для фильтрации событий
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' обозначает UTC время
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        await update.message.reply_text(f"У вас нет предстоящих событий")
        return ConversationHandler.END

    events_info = []
    for event in events:
        event_id = event['id']
        event_summary = event.get('summary', 'Без названия')
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        events_info.append((event_id, event_summary, event_start))

    res = events_info

    ans = "Вот список предстоящих событий:\n"
    i = 1
    for event_id, summary, start in res:
        start_dt = datetime.fromisoformat(start[:-6])
        start2 = start_dt.strftime("%d %B %Y %H:%M")
        ans += f'''{i}. "{summary}"\n Начало: {start2}\n\n'''
        i += 1

    ans +=  "\nУправеление встречами /meets \nПосмотр списка команд /help"
    await update.message.reply_text(ans)  # Пример ответа
    return ConversationHandler.END


async def edit_meet(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text("Выберите встречу для редактирования...")  # Пример ответа
    return ConversationHandler.END


async def delete_meet(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_email = get_email_by_user(user.username)
    if not user:
        await update.message.reply_text(f"Пользователь с email {user_email} не найден в базе данных.")
        return ConversationHandler.END

    user = get_user_by_email(user_email)
    user_id = user[0]
    calendar_id = user[3]  # GoogleCalendarLink

    if not calendar_id:
        await update.message.reply_text(f"Вы не привязали календарь, сначала привяжите его. \start")
        return ConversationHandler.END

    creds = get_credentials(user_id)

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' обозначает UTC время
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        await update.message.reply_text(f"У вас нет предстоящих событий")
        return ConversationHandler.END

    events_info = []
    for event in events:
        event_id = event['id']
        event_summary = event.get('summary', 'Без названия')
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        events_info.append((event_id, event_summary, event_start))

    res = events_info

    ans = "Вот список предстоящих событий:\n"
    i = 1
    for event_id, summary, start in res:
        start_dt = datetime.fromisoformat(start[:-6])
        start2 = start_dt.strftime("%d %B %Y %H:%M")
        ans += f'''{i}. "{summary}"\n Начало: {start2}\n\n'''
        i += 1
    ans += "\n Выберите встречу для удаления, введите её название:"
    await update.message.reply_text(ans)
    return DELETE_MEET

# Другая функция для обработки ID события
async def handle_delete_meet(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_email = get_email_by_user(user.username)
    event_name = update.message.text
    event_id = -1

    user = get_user_by_email(user_email)
    user_id = user[0]
    calendar_id = user[3]

    creds = get_credentials(user_id)
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' обозначает UTC время
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        event_summary = event.get('summary', 'Без названия')
        if event_summary == event_name:
            event_id = event['id']

    if event_id == -1 :
        await update.message.reply_text(f'''Событие с названием "{event_name}" не найдено. Введите название повторно. Или отмените действие /cancel.''')
        return DELETE_MEET

    success, message = delete_event(user_email, event_id)
    await update.message.reply_text(message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_meet_handler():
    return ConversationHandler(
        entry_points=[
                      CommandHandler("meets", meets),
                      CommandHandler("get_meets", get_meets),
                      CommandHandler("edit_meet", edit_meet),
                      CommandHandler("delete_meet", delete_meet),
                      ],
        states={
            DELETE_MEET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_meet)],
        },
    fallbacks=[CommandHandler("cancel", cancel)],
)
