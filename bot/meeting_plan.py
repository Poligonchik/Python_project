from time import sleep

from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from datetime import datetime, timedelta, timezone
from calendar import monthrange
from googleapiclient.discovery import build

from bot.databases_methods.db_sleep_time import get_sleep_time
from bot.edit_command import CHOICE
from bot.google_calendar.google_calendar import create_event, get_credentials
from bot.databases_methods.db_user import get_user_id_by_telegram_id, get_user_by_link, get_user_by_email
from bot.databases_methods.db_statistic import init_db_statistic, create_statistic, add_time_to_alltime, user_id_exist
from bot.databases_methods.db_meet import create_meet
from bot.databases_methods.db_team import create_team
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
(SET_EVENT_TITLE_MP, SET_EVENT_DESCRIPTION_MP, CHOICE_WAY_TO_CREATE_TIME, AUTOMAT_SET_TIME,
 SET_EVENT_PARTICIPANTS_MP, SET_EVENT_START_MP,
 SET_EVENT_START_TIME_MP, SET_EVENT_END_DATE_MP, SET_EVENT_END_TIME_MP) = range(10, 19)

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
    await update.message.reply_text("Введите описание встречи, если не хотите его добавлять введите -:")
    return SET_EVENT_DESCRIPTION_MP

async def set_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text.strip()
    if description == "-":
        description = ""

    context.user_data['event_description'] = description  # Сохраняем описание события
    await update.message.reply_text("Если хотите добавить участников, ввведите email участников встречи через запятую (например, email1@example.com, email2@example.com). Иначе введите -.")
    return SET_EVENT_PARTICIPANTS_MP


def get_year_buttons():
    """Кнопки для выбора года."""
    current_year = datetime.now().year
    years = [str(year) for year in range(current_year, current_year + 5)]
    keyboard = [[InlineKeyboardButton(year, callback_data=f"year_{year}") for year in years]]
    return InlineKeyboardMarkup(keyboard)

def get_month_buttons(year):
    """Кнопки для выбора месяца."""
    year = int(year)
    if year == datetime.now().year:
        months = [f"{month:02}" for month in range(datetime.now().month, 13)]
    else:
        months = [f"{month:02}" for month in range(1, 13)]
    keyboard = [
        [InlineKeyboardButton(month, callback_data = f"month_{month}") for month in months[i:i + 4]]
        for i in range(0, len(months), 4)
    ]
    return InlineKeyboardMarkup(keyboard)

def get_day_buttons(year, month):
    """Кнопки для выбора дня."""
    year = int(year)
    month = int(month)
    _, days_in_month = monthrange(year, month) # количество дней в месяце
    if year == datetime.now().year and month == datetime.now().month:
        days = [f"{day:02}" for day in range(datetime.now().day, days_in_month + 1)]
    else:
        days = [f"{day:02}" for day in range(1, days_in_month + 1)]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days[i:i+7]] for i in range(0, len(days), 7)]
    return InlineKeyboardMarkup(keyboard)

async def set_event_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    participants = update.message.text.strip().split(",")  # Разделяем email через запятую
    participants = [email.strip() for email in participants if email.strip()]  # Убираем лишние пробелы и пустые строки

    if update.message.text.strip() == "-":
        participants = []

    context.user_data['participants'] = participants  # Сохраняем список email

    # Выбор года

    await update.message.reply_text(
        "Вы можете самостоятельно назначить время встречи для этого введите - 1. Или установить время встречи автоматически. Программа поставит встречу, на ближайшее время, в которое свободен каждый участник встречи. Для этого введите - 2.")
    return CHOICE_WAY_TO_CREATE_TIME


async def choice_way_to_create_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "1":
        await update.message.reply_text("Выберите год начала встречи:", reply_markup=get_year_buttons())
        return SET_EVENT_START_MP
    else:
        await update.message.reply_text("Напишите продолжительность встречи в минутах. Целое число например 120")
        return AUTOMAT_SET_TIME

async def auto_set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meet_time = update.message.text
    try:
        meet_time = int(meet_time)
    except ValueError:
        await update.message.reply_text("Вы ввели некорректный запрос. Напишите продолжительность встречи в минутах (целое число)")
        return AUTOMAT_SET_TIME

    summary = context.user_data.get('event_title')
    description = context.user_data.get('event_description')
    now = datetime.utcnow().isoformat() + 'Z'
    start_time = now
    end_time = now
    participants = context.user_data.get('participants', [])
    user_id = get_user_id_by_telegram_id(update.message.from_user.username)

    user = get_user_by_link(update.message.from_user.username)
    creator_email = user[3]

    if creator_email not in participants:
        participants.append(creator_email)

    if not user:
        await update.message.reply_text(f"Пользователь с email {creator_email} не найден в базе данных.")
        return ConversationHandler.END

    user_id = user[0]
    calendar_id = user[3]  # GoogleCalendarLink

    if not calendar_id:
        await update.message.reply_text(f"Вы не привязали календарь, сначала привяжите его. \start")
        return ConversationHandler.END

    creds = get_credentials(user_id)
    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(calendarId=calendar_id, timeMin=now, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    skan_line = []

    sleep_time = get_sleep_time(user_id)

    sleep_start = datetime.strptime(sleep_time[1], "%Y-%m-%d %H:%M:%S").time()
    sleep_end = datetime.strptime(sleep_time[2], "%Y-%m-%d %H:%M:%S").time()

    if (sleep_time[1] != sleep_time[2]) and ((24 * 60 - sleep_end.hour * 60 - sleep_end.minute + sleep_start.hour * 60 + sleep_start.minute) % (24 *60) < meet_time):
        response_message = f"Ошибка создания встречи. Встреча длится дольше, чем бодрствует {creator_email}\n\nДля создания еще одной встречи введите /create_meeting\nДля просмотра списка команд введите /help."

        await update.message.reply_text(response_message)
        return ConversationHandler.END



    temp_date = datetime.now().date()
    temp_datetime = datetime.combine(temp_date, datetime.min.time())

    if sleep_start < sleep_end:
        for i in range(-1, 1500):
            time_delta_d = timedelta(days=i)

            temp = (str(temp_datetime + time_delta_d + timedelta(hours=sleep_start.hour, minutes=sleep_start.minute)), 1)
            skan_line.append(temp)

            temp = (str(temp_datetime + time_delta_d + timedelta(hours=sleep_end.hour, minutes=sleep_end.minute)), -1)
            skan_line.append(temp)

    if sleep_start > sleep_end:
        for i in range(-1, 1500):
            time_delta_d = timedelta(days=i)

            temp = (str(temp_datetime + time_delta_d + timedelta(hours=sleep_start.hour, minutes=sleep_start.minute)), 1)
            skan_line.append(temp)

            temp = (str(temp_datetime + time_delta_d + timedelta(days=1) + timedelta(hours=sleep_end.hour, minutes=sleep_end.minute)), -1)
            skan_line.append(temp)

    for event in events:
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        event_end = event['end'].get('dateTime', event['end'].get('date'))

        temp = (event_start, 1)
        skan_line.append(temp)
        temp = (event_end, -1)
        skan_line.append(temp)

    skan_line.sort(key=lambda x: x[0])

    count = 0
    f = 0

    for i in range(len(skan_line) - 1):
        count += skan_line[i][1]
        time1 = datetime.fromisoformat(skan_line[i][0])
        time2 = datetime.fromisoformat(skan_line[i + 1][0])

        time1 = time1.replace(tzinfo=timezone(timedelta(hours=3)))
        time2 = time2.replace(tzinfo=timezone(timedelta(hours=3)))

        time_diff = (time2 - time1).total_seconds() / 60
        noww = datetime.now()
        noww = noww.replace(tzinfo=timezone(timedelta(hours=3)))
        if  time1 > noww and count == 0 and time_diff > meet_time:
            f = 1
            time_delta_s = timedelta(minutes=1)
            start_time = time1 + time_delta_s
            time_delta = timedelta(minutes=(meet_time))
            end_time = start_time + time_delta
            break

    if f == 0:
        if len(skan_line):
            time_delta_s = timedelta(minutes=1)
            start_time = datetime.fromisoformat(skan_line[len(skan_line) - 1][0]) + time_delta_s
            time_delta = timedelta(minutes=(meet_time))
            end_time = start_time + time_delta
        else:
            time_delta_s = timedelta(minutes=1)
            start_time = datetime.now() + time_delta_s
            time_delta = timedelta(minutes=(meet_time))
            end_time = start_time + time_delta


    meet_id = create_meet(summary, description, start_time, end_time)

    for mail in participants:
        create_team(meet_id, mail)

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

    start2 = start_time.strftime("%d %B %Y %H:%M")
    response_message = f'''Создана встреча "{summary}". Встреча начнется в {start2}.\nДобавлены следующие пользователи:\n'''
    if successful_additions:
        response_message += "\n".join(successful_additions)

    if failed_additions:
        response_message += "\n\nНе удалось создать встречу для следующих пользователей:\n"
        response_message += "\n".join(failed_additions)

    response_message += "\n\nДля создания еще одной встречи введите /create_meeting\nДля просмотра списка команд введите /help"
    meeting_duration = meet_time * 60 * 60

    if not user_id_exist(user_id):
        create_statistic(user_id)

    add_time_to_alltime(user_id, meeting_duration)

    await update.message.reply_text(response_message)
    return ConversationHandler.END


async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор года, месяца и дня для НАЧАЛА встречи."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_data = context.user_data

    if data.startswith("year_"):
        user_data['year'] = data.split("_")[1]
        await query.edit_message_text(f"Год выбран: {user_data['year']}\nТеперь выберите месяц:",
                                      reply_markup=get_month_buttons(user_data['year']))
    elif data.startswith("month_"):
        user_data['month'] = data.split("_")[1]
        await query.edit_message_text(f"Месяц выбран: {user_data['year']}.{user_data['month']:02}\nТеперь выберите день:",
                                      reply_markup=get_day_buttons(user_data['year'], user_data['month']))
    elif data.startswith("day_"):
        user_data['day'] = data.split("_")[1]
        await query.edit_message_text(f"День выбран: {user_data['year']}.{user_data['month']:02}.{user_data['day']:02}\n"
                                      "Теперь введите время вручную в формате ЧЧ:ММ (например, 17:45):")
        return SET_EVENT_START_TIME_MP

async def set_event_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод времени НАЧАЛА вручную."""
    time_input = update.message.text.strip()
    try:
        # Проверяем формат времени ЧЧ:ММ
        hour, minute = map(int, time_input.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            user_data = context.user_data
            # Сохраняем дату и время начала
            start_time_str = f"{user_data['year']}-{user_data['month']}-{user_data['day']} {hour:02}:{minute:02}"
            user_data['event_start_time'] = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")

            # Переход к выбору даты окончания
            await update.message.reply_text(
                f"Дата начала встречи: {user_data['event_start_time'].strftime('%Y-%m-%d %H:%M')}. \nТеперь выберите год окончания встречи",
                reply_markup=get_year_buttons()
            )
            return SET_EVENT_END_DATE_MP
        else:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("Некорректный формат времени. Введите время в формате ЧЧ:ММ (например, 17:45):")
        return SET_EVENT_START_TIME_MP

async def handle_end_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор года, месяца и дня для ОКОНЧАНИЯ встречи."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_data = context.user_data

    start_year = user_data['event_start_time'].year
    start_month = user_data['event_start_time'].month
    start_day = user_data['event_start_time'].day

    if data.startswith("year_"):
        selected_year = int(data.split("_")[1])  # год окончания

        # Проверяем корректность
        if selected_year < start_year:
            await query.edit_message_text(
                f"Ошибка: год окончания не может быть раньше года начала ({start_year}).\nПопробуйте выбрать корректный год.",
                reply_markup=get_year_buttons()
            )
            return  # Возвращаем управление

        # Сохраняем выбранный год окончания
        user_data['end_year'] = selected_year
        await query.edit_message_text(
            f"Год окончания выбран: {user_data['end_year']}\nТеперь выберите месяц:",
            reply_markup=get_month_buttons(user_data['end_year'])  # Переходим к выбору месяца
        )
    elif data.startswith("month_"):
        user_data['end_month'] = int(data.split("_")[1])
        if start_year == user_data['end_year'] and start_month > user_data['end_month']:
            await query.edit_message_text(
                f"Ошибка: дата окончания не может быть раньше даты начала ({start_year}.{start_month:02}).\nПопробуйте выбрать корректный месяц.",
                reply_markup = get_month_buttons(user_data['end_year'])  # Возвращаем кнопки для выбора месяца
            )
            return  # Возвращаем управление
        await query.edit_message_text(f"Месяц окончания выбран: {user_data['end_year']}.{user_data['end_month']:02}\nТеперь выберите день:",
                                      reply_markup=get_day_buttons(user_data['end_year'], user_data['end_month']))
    elif data.startswith("day_"):
        user_data['end_day'] = int(data.split("_")[1])
        if start_year == user_data['end_year'] and start_month == user_data['end_month'] and start_day > user_data['end_day']:
            await query.edit_message_text(
                f"Ошибка: дата окончания не может быть раньше даты начала ({start_year}.{start_month:02}.{start_day:02}).\nПопробуйте выбрать корректный день.",
                reply_markup = get_day_buttons(user_data['end_year'], user_data['end_month'])  # Возвращаем кнопки для выбора года
            )
            return
        await query.edit_message_text(
            f"День окончания выбран: {user_data['end_year']}.{user_data['end_month']:02}.{user_data['end_day']}\n"
            "Теперь введите время вручную в формате ЧЧ:ММ (например, 18:45):"
        )
        return SET_EVENT_END_TIME_MP

async def set_event_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод времени окончания вручную."""
    time_input = update.message.text.strip()
    try:
        # Проверяем формат времени ЧЧ:ММ
        hour, minute = map(int, time_input.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            user_data = context.user_data
            # Собираем полную дату и время окончания
            end_time_str = f"{user_data['end_year']}-{user_data['end_month']}-{user_data['end_day']} {hour:02}:{minute:02}"
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")

            # Проверяем, что время окончания позже времени начала
            if end_time <= user_data['event_start_time']:
                await update.message.reply_text("Время окончания должно быть позже времени начала. Попробуйте ещё раз:")
                return SET_EVENT_END_TIME_MP

            user_data['event_end_time'] = end_time
            await handle_create_event(update, context)  # Переход к созданию события
            return ConversationHandler.END
        else:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("Некорректный формат времени. Введите время в формате ЧЧ:ММ (например, 18:45):")
        return SET_EVENT_END_TIME_MP

async def handle_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = context.user_data.get('event_title')
    description = context.user_data.get('event_description')
    start_time = context.user_data.get('event_start_time')
    end_time = context.user_data.get('event_end_time')
    participants = context.user_data.get('participants', [])
    meet_id = create_meet(summary, description, start_time, end_time)

    user_id = get_user_id_by_telegram_id(update.message.from_user.username)

    user = get_user_by_link(update.message.from_user.username)
    creator_email = user[3]

    if creator_email not in participants:
        participants.append(creator_email)

    for mail in participants:
        create_team(meet_id, mail)

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

    response_message += "\n\nДля добавления новой встречи нажмите /create_meeting \nДля просмотра доступных команд /help"
    meeting_duration = int((end_time - start_time).total_seconds() // 60)

    if not user_id_exist(user_id):
        create_statistic(user_id)

    add_time_to_alltime(user_id, meeting_duration)

    await update.message.reply_text(response_message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Для добавления новой встречи нажмите /create_meeting \nДля просмотра доступных команд /help", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_meeting_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("create_meeting", create_meeting),
        ],
        states={
            SET_EVENT_TITLE_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_title)],
            SET_EVENT_DESCRIPTION_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_description)],
            CHOICE_WAY_TO_CREATE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice_way_to_create_time)],
            AUTOMAT_SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, auto_set_time)],
            SET_EVENT_PARTICIPANTS_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_participants)],
            SET_EVENT_START_MP: [CallbackQueryHandler(handle_time_selection)],
            SET_EVENT_START_TIME_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_start_time)],
            SET_EVENT_END_DATE_MP: [CallbackQueryHandler(handle_end_date_selection)],
            SET_EVENT_END_TIME_MP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_event_end_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
