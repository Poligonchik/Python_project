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


import os
import pickle

# Области доступа
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Этапы диалога
(START, CHOICE, MEETING_OPTION, SET_EVENT_TITLE, SET_EVENT_DESCRIPTION,
 SET_EVENT_PARTICIPANTS, SET_EVENT_START, SET_EVENT_END, AUTH) = range(9)

# Функции для работы с базой данных (предполагается, что они уже реализованы)
from bot.databases_methods.db_user import (
    init_db_user,
    add_user,
    get_user_by_link,
    edit_user_name,
    get_user_calendar_id,
    get_user_id_by_telegram_id
)

from bot.databases_methods.db_user import edit_user_calendar_id
from bot.databases_methods.db_meet import init_db_meet, create_meet
from bot.databases_methods.db_team import init_db_team, create_team
from bot.databases_methods.db_statistic import init_db_statistic, create_statistic, add_time_to_alltime
from bot.databases_methods.db_sleep_time import init_db_sleep_time, create_sleep_time, edit_sleep_time_to, edit_sleep_time_from
from bot.databases_methods.db_black_list import init_db_black_list, create_block

from bot.edit_command import get_edit_handler

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функции для извлечения и сохранения Calendar ID
def extract_calendar_id(url):
    from urllib.parse import urlparse, parse_qs
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        cid = query_params.get('cid')
        if cid:
            logger.info(f"Извлечённый Calendar ID: {cid[0]}")
            return cid[0]
    except Exception as e:
        logger.error(f"Ошибка извлечения Calendar ID: {e}")
    return None


def get_credentials(user_id):
    creds_path = f"bot/token_{user_id}.pickle"
    if os.path.exists(creds_path):
        logger.info(f"Токен найден для пользователя {user_id}")
        with open(creds_path, 'rb') as token:
            creds = pickle.load(token)
        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(user_id, creds)
        return creds
    else:
        logger.warning(f"Токен отсутствует для пользователя {user_id}")
    return None

def save_credentials(user_id, creds):
    creds_path = f"bot/token_{user_id}.pickle"
    with open(creds_path, 'wb') as token:
        pickle.dump(creds, token)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    telegram_link = user.username if user.username else user.id

    curr_user = get_user_by_link(telegram_link)
    if curr_user:
        calendar_id = curr_user[3]  # Поле GoogleCalendarLink
        if calendar_id:
            await update.message.reply_text(
                f"Привет, {curr_user[1]}! Ваш календарь уже привязан.",
                reply_markup=ReplyKeyboardMarkup(
                    [["Добавить встречу", "Статистика"]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
            )
        else:
            await update.message.reply_text(
                "Вы зарегистрированы, но не привязали календарь. Пришлите ссылку на ваш Google Календарь."
            )
    else:
        await update.message.reply_text(
            f"Здравствуйте, {user.full_name}, чтобы использовать бота, пришлите ссылку на ваш Google Календарь."
        )
        user_id = add_user(user.full_name, telegram_link, "")
        create_statistic(user_id)
        create_sleep_time(user_id)
        await update.message.reply_text(f"Вы зарегистрированы с ID {user_id}.")
    return CHOICE

# Выбор действия
# Выбор действия
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    logger.info(f"Выбранный текст: {text}")
    if text.startswith("https://"):
        return await handle_calendar_url(update, context)
    elif text == "Добавить встречу":
        # Переход в создание встречи
        return await create_meeting(update, context)
    elif text == "Статистика":
        await update.message.reply_text("Функционал статистики пока не реализован.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Выберите действие или отправьте ссылку на календарь.")
        return CHOICE


# Обработка ссылки на календарь
async def handle_calendar_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ссылку на Google Календарь и привязывает её к пользователю.
    """
    telegram_username = update.message.from_user.username  # Берём username из Telegram
    logger.info(f"Telegram username: {telegram_username}")
    if not telegram_username:
        await update.message.reply_text(
            "Ваш Telegram аккаунт не имеет username. Пожалуйста, задайте username в настройках Telegram."
        )
        return CHOICE

    # Получаем UserId из базы данных
    user_id = get_user_id_by_telegram_id(telegram_username)
    logger.info(f"UserId из базы: {user_id}")
    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе данных.")
        return CHOICE

    # Извлечение Calendar ID из ссылки
    url = update.message.text.strip()
    calendar_id = extract_calendar_id(url)
    if not calendar_id:
        await update.message.reply_text(
            "Не удалось распознать Calendar ID. Пожалуйста, отправьте корректную ссылку на Google Календарь."
        )
        return CHOICE

    # Получение токена пользователя
    creds = get_credentials(user_id)
    if not creds or not creds.valid:
        # Если токен недействителен, запрашиваем авторизацию
        flow = InstalledAppFlow.from_client_secrets_file('bot/calendari.json', SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

        context.user_data['flow'] = flow
        context.user_data['calendar_id'] = calendar_id

        await update.message.reply_text(
            f"Пожалуйста, авторизуйте доступ к вашему Google Календарю, перейдя по ссылке:\n{auth_url}\n"
            f"После авторизации введите полученный код сюда."
        )
        return AUTH  # Переход в состояние ожидания кода авторизации

    # Сохраняем Calendar ID в базе данных
    edit_user_calendar_id(user_id, calendar_id)
    await update.message.reply_text("Ваш календарь успешно привязан!")
    return CHOICE




# Обработка кода OAuth
async def handle_oauth_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    code = update.message.text.strip()
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)  # Получаем UserId из базы

    if not user_id:
        await update.message.reply_text("Пользователь не найден в базе данных.")
        logger.error(f"UserId равен None для пользователя с Telegram username: {telegram_username}")
        return CHOICE

    flow = context.user_data.get('flow')
    calendar_id = context.user_data.get('calendar_id')

    if not flow:
        await update.message.reply_text(
            "Не удалось найти активный OAuth процесс. Попробуйте снова отправить ссылку на календарь."
        )
        return CHOICE

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        logger.info(f"Сохраняем токен для UserId: {user_id}")
        save_credentials(user_id, creds)  # Сохраняем токен под UserId

        edit_user_calendar_id(user_id, calendar_id)
        await update.message.reply_text("Авторизация прошла успешно!")
        return CHOICE
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {e}")
        await update.message.reply_text("Ошибка при авторизации. Попробуйте снова.")
        return CHOICE




# Функция для создания события
# Функция для создания события
def create_event(creds, calendar_id, summary, description, start_time, end_time, attendees_emails=None):
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Europe/Moscow'},
        'end': {'dateTime': end_time, 'timeZone': 'Europe/Moscow'},
    }
    if attendees_emails:
        event['attendees'] = [{'email': email} for email in attendees_emails]
    return service.events().insert(calendarId=calendar_id, body=event).execute()



# Команда для создания встречи
# Команда для создания встречи
async def create_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)  # Получаем UserId из базы
    creds = get_credentials(user_id)
    calendar_id = get_user_calendar_id(user_id)

    if not creds or not creds.valid:
        await update.message.reply_text("Сначала авторизуйте доступ к вашему Google Календарю.")
        return CHOICE

    if not calendar_id:
        await update.message.reply_text("Не найден Calendar ID. Пожалуйста, отправьте ссылку на ваш Google Календарь.")
        return CHOICE

    # Сохраняем UserId инициатора и Calendar ID в user_data
    context.user_data['user_id'] = user_id
    context.user_data['calendar_id'] = calendar_id

    await update.message.reply_text("Введите название встречи:")
    return SET_EVENT_TITLE


async def set_event_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    participants = update.message.text.strip().split(",")  # Разделяем email через запятую
    participants = [email.strip() for email in participants if email.strip()]  # Убираем лишние пробелы и пустые строки
    context.user_data['participants'] = participants  # Сохраняем список email

    if not participants:
        await update.message.reply_text(
            "Вы не ввели ни одного участника. Если хотите добавить участников, введите их email через запятую. Если нет, просто отправьте пустое сообщение.")

    await update.message.reply_text(
        "Введите дату и время начала встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-10 14:30):")
    return SET_EVENT_START

# Новый этап: Установка названия события
async def set_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data['event_title'] = title  # Сохраняем название события
    await update.message.reply_text("Введите описание встречи (или оставьте пустым):")
    return SET_EVENT_DESCRIPTION


# Новый этап: Установка описания события
async def set_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text.strip()
    context.user_data['event_description'] = description  # Сохраняем описание события
    await update.message.reply_text("Введите email участников встречи через запятую (например, email1@example.com, email2@example.com):")
    return SET_EVENT_PARTICIPANTS


# Новый этап: Установка времени начала встречи
async def set_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time_str = update.message.text.strip()
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        context.user_data['event_start_time'] = start_time
        await update.message.reply_text("Введите дату и время окончания встречи в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-10 15:30):")
        return SET_EVENT_END
    except ValueError:
        await update.message.reply_text("Некорректный формат времени. Попробуйте ещё раз.")
        return SET_EVENT_START


async def set_event_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    end_time_str = update.message.text.strip()
    telegram_username = update.message.from_user.username
    user_id = get_user_id_by_telegram_id(telegram_username)

    try:
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
        start_time = context.user_data['event_start_time']
        if end_time <= start_time:
            await update.message.reply_text("Время окончания должно быть позже времени начала. Попробуйте ещё раз.")
            return SET_EVENT_END

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
        return SET_EVENT_END
    except Exception as e:
        logger.error(f"Ошибка при создании события: {e}")
        await update.message.reply_text(f"Ошибка при создании события: {e}")
        return ConversationHandler.END


# Выбор метода добавления встречи
async def meeting_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    telegram_username = update.message.from_user.username  # Получаем username пользователя
    user_id = get_user_id_by_telegram_id(telegram_username)  # Получаем UserId из базы

    creds = get_credentials(user_id)
    calendar_id = get_user_calendar_id(user_id)

    if not creds or not creds.valid:
        await update.message.reply_text("Сначала авторизуйте доступ к вашему Google Календарю.")
        return ConversationHandler.END

    if not calendar_id:
        await update.message.reply_text("Не найден Calendar ID. Отправьте ссылку на ваш Google Календарь.")
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

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Список команд:\n/start - начать\n/help - помощь\n/edit - редактировать\n/статистика - статистика\n/создать_встречу - добавить встречу")

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(get_edit_handler())

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            MEETING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, meeting_option)],
            SET_EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_title)],
            SET_EVENT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_description)],
            SET_EVENT_PARTICIPANTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_participants)],
            SET_EVENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_start)],
            SET_EVENT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_end)],
            AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_oauth_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("create_meeting", create_meeting))

    print("Бот запущен!")
    app.run_polling()
