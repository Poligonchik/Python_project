from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

# Этапы диалога
from bot.constants import START, CHOICE, AUTH, SET_TIME, MEETING_OPTION

from bot.databases_methods.db_user import (init_db_user, add_user, get_user_by_link, edit_user_name,
                                           get_user_calendar_id, get_user_id_by_telegram_id, edit_user_calendar_id)
from bot.databases_methods.db_meet import init_db_meet, create_meet
from bot.databases_methods.db_team import init_db_team, create_team
from bot.databases_methods.db_statistic import init_db_statistic, create_statistic, add_time_to_alltime
from bot.databases_methods.db_sleep_time import init_db_sleep_time, create_sleep_time, edit_sleep_time_to, edit_sleep_time_from
from bot.databases_methods.db_black_list import init_db_black_list, create_block

from bot.edit_command import get_edit_handler
from bot.help_handler import help_command
from bot.meets_handler import get_meet_handler
from bot.google_calendar.google_calendar import extract_calendar_id, get_credentials, save_credentials, create_event
from bot.google_calendar.handlers_calendar import handle_calendar_url, handle_oauth_code
from bot.meeting_plan import create_meeting, get_meeting_handler, start_meeting

from bot.send_statistic import get_statistic

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    telegram_link = user.username if user.username else user.id

    curr_user = get_user_by_link(telegram_link)
    if curr_user:
        calendar_id = curr_user[3]  # Поле GoogleCalendarLink
        if calendar_id:
            await update.message.reply_text(
                f"Привет, {curr_user[1]}! Ваш календарь уже привязан. Нажмите /help для просмотра команд",
                reply_markup=ReplyKeyboardMarkup(
                    [["Добавить встречу", "Статистика", "Редактировать профиль"]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
            )
        else:
            await update.message.reply_text(
                "Вы зарегистрированы, но не привязали календарь. Пришлите идентификатор календаря (почту, к которой привязан гугл календарь), чтобы продолжать работу."
            )
    else:
        await update.message.reply_text(
            f"Здравствуйте, {user.full_name}, чтобы использовать бота, пришлите идентификатор календаря. "
            f"Для главного календаря это ваша почта, а для остальных перейдите в настройки календаря -> "
            f"Интеграция календаря -> Идентификатор календаря"
        )
        user_id = add_user(user.full_name, telegram_link, "")
        create_statistic(user_id)
        create_sleep_time(user_id)
    return CHOICE

# Выбор действия
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    logger.info(f"Выбранный текст: {text}")
    if text == "Добавить встречу":
        await update.message.reply_text("Для подтверждения нажмите --> /create_meeting")
        return ConversationHandler.END
    elif text == "Статистика":
        await get_statistic(update, context)
        return ConversationHandler.END
    else:
        return await handle_calendar_url(update, context)


# Выбор метода добавления встречи
async def meeting_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    telegram_username = update.message.from_user.username  # Получаем username пользователя
    user_id = get_user_id_by_telegram_id(telegram_username)  # Получаем UserId из базы

    creds = get_credentials(user_id)
    calendar_id = get_user_calendar_id(user_id)

    if not creds or not creds.valid:
        await update.message.reply_text("Сначала настройте доступ к вашему Google Календарю.")
        return ConversationHandler.END

    if not calendar_id:
        await update.message.reply_text("Не найден Calendar ID. Отправьте идентификатор Google Календаря.")
        return CHOICE

    if text == "Автоустановка времени":
        try:
            start_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0,
                                                                      microsecond=0).isoformat()
            end_time = (datetime.now() + timedelta(days=1)).replace(hour=11, minute=0, second=0,
                                                                    microsecond=0).isoformat()
            event = create_event(creds, calendar_id, start_time=start_time, end_time=end_time)
            await update.message.reply_text(f"Событие успешно создано: {event.get('htmlLink')}")
        except Exception as e:
            logger.error(f"Ошибка при создании события: {e}")
            await update.message.reply_text(f"Ошибка при создании события: {e}")
        return ConversationHandler.END

    elif text == "Ввести время вручную":
        await update.message.reply_text("Введите время встречи в формате ЧЧ:ММ (например, 14:30):")
        return SET_TIME
    else:
        await update.message.reply_text("Выберите одну из предложенных опций.")
        return MEETING_OPTION


# Установка времени вручную
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_time = update.message.text.strip()
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)
    creds = get_credentials(user_id)
    calendar_id = get_user_calendar_id(user_id)

    try:
        meeting_date = datetime.now().date() + timedelta(days=1)
        start_time = datetime.strptime(f"{meeting_date} {user_time}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(hours=1)

        event = create_event(creds, calendar_id, start_time=start_time.isoformat(), end_time=end_time.isoformat())
        await update.message.reply_text(f"Встреча создана: {event.get('htmlLink')}")
    except Exception as e:
        logger.error(f"Ошибка при создании встречи: {e}")
        await update.message.reply_text("Ошибка: проверьте формат времени или доступы.")
    return ConversationHandler.END

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. До встречи!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основная функция
if __name__ == "__main__":
    # Инициализация базы данных
    init_db_user()
    init_db_meet()
    init_db_team()
    init_db_statistic()
    init_db_sleep_time()
    init_db_black_list()

    # Создание приложения Telegram бота
    TELEGRAM_TOKEN = "7594370282:AAGpyh78Cr9TXqWyxYlBBJDv_BN34V2e5Jw"  # Замените на ваш токен
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    app.add_handler(help_command())
    app.add_handler(get_edit_handler())
    app.add_handler(get_meeting_handler())
    app.add_handler(get_meet_handler())

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            MEETING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, meeting_option)],
            SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
            AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_oauth_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен!")
    app.run_polling()
