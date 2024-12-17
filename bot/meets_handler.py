from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters, CallbackContext, MessageHandler, ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from bot.google_calendar.google_calendar import get_credentials, build
from bot.databases_methods.db_user import get_email_by_user, get_user_by_email
async def meets(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text('''Выберите действие:
    /get_meets - просмотр ожидаемых событий
    /edit_meet - редактировать встречу
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

    events_result = service.events().list(calendarId=calendar_id, maxResults=10).execute()
    events = events_result.get('items', [])

    if not events:
        await update.message.reply_text(f"У вас нет предстоящих событий")
        return ConversationHandler.END

    events_info = []
    for event in events:
        event_id = event['id']
        event_summary = event.get('summary', 'Без названия')
        events_info.append((event_id, event_summary))

    res = events_info

    ans = "Ваш список встреч:\n"
    i = 1
    for event_id, summary in res:
        ans += f"{i}. {summary}\n"
        i += 1
    await update.message.reply_text(ans)  # Пример ответа
    return ConversationHandler.END


async def edit_meet(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text("Выберите встречу для редактирования...")  # Пример ответа
    return ConversationHandler.END


async def delete_meet(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text("Выберите встречу для удаления...")  # Пример ответа
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

        },
    fallbacks=[CommandHandler("cancel", cancel)],
)
