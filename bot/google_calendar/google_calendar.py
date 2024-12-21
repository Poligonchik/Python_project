from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import os
import pickle
import logging
from bot.databases_methods.db_sleep_time import get_sleep_time
from bot.databases_methods.db_user import get_user_by_email, get_user_calendar_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Области доступа
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Функции для извлечения и сохранения Calendar ID
def extract_calendar_id(url):
    try:
        parse = urlparse(url)
        query = parse_qs(parse.query)
        cid = query.get('cid')      # у нас тут строка запроса, в данном случае cid=...
        if cid:
            logger.info(f"Извлечённый Calendar ID: {cid[0]}")
            return cid[0]
    except Exception as e:
        logger.error(f"Ошибка извлечения Calendar ID: {e}")
    return None

# Получение учетных данных
def get_credentials(user_id):
    token_path = f"bot/token_{user_id}.pickle"  # Путь к токену
    if os.path.exists(token_path):
        logger.info(f"Токен найден для пользователя {user_id}")
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)          # Загружаем токен
        if not creds.valid and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())              # Если токен истек, обновляем
                save_credentials(user_id, creds)      # и сохраняем
            except Exception as e:
                logger.error(f"Ошибка обновления токена для пользователя {user_id}: {e}")
                return None
        return creds
    else:
        logger.warning(f"Токен отсутствует для пользователя {user_id}")
    return None

# Сохраняем новый токен
def save_credentials(user_id, creds):
    token_path = f"bot/token_{user_id}.pickle"
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)   # Берет creds и записывает в token

# Функция для создания события в календаре пользователя
def create_event(user_email, summary, description, start_time, end_time):
    user = get_user_by_email(user_email)
    if not user:
        logger.warning(f"Пользователь с email {user_email} не найден в базе данных.")
        return False, f"Пользователь с email {user_email} не найден."

    user_id = user[0]
    calendar_id = user[3]  # GoogleCalendarLink
    if not calendar_id:
        logger.warning(f"У пользователя {user_email} не привязан календарь.")
        return False, f"У пользователя {user_email} не привязан календарь."

    # Проверка времени сна
    '''
    sleep_time = get_sleep_time(user_id)
    if sleep_time:
        sleep_start = datetime.strptime(sleep_time[1], "%Y-%m-%d %H:%M:%S")
        sleep_end = datetime.strptime(sleep_time[2], "%Y-%m-%d %H:%M:%S")
        event_start = datetime.fromisoformat(start_time)
        event_end = datetime.fromisoformat(end_time)

        if (event_start < sleep_end) and (event_end > sleep_start):
            logger.info(f"Событие перекрывается с временем сна пользователя {user_email}. Пропуск.")
            return False, f"Событие перекрывается с временем сна пользователя {user_email}."
    '''
    creds = get_credentials(user_id)
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Europe/Moscow'},
        'end': {'dateTime': end_time, 'timeZone': 'Europe/Moscow'},
    }

    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Событие добавлено в календарь {user_email}: {created_event.get('htmlLink')}")
        return True, f"Событие добавлено в календарь {user_email}."
    except Exception as e:
        logger.error(f"Ошибка при добавлении события в календарь {user_email}: {e}")
        return False, f"Ошибка при добавлении события в календарь {user_email}: {e}"

def delete_event(user_email, event_id):
    user = get_user_by_email(user_email)
    if not user:
        logger.warning(f"Пользователь с email {user_email} не найден в базе данных.")
        return False, f"Пользователь с email {user_email} не найден."

    user_id = user[0]
    calendar_id = user[3]  # GoogleCalendarLink
    if not calendar_id:
        logger.warning(f"У пользователя {user_email} не привязан календарь.")
        return False, f"У пользователя {user_email} не привязан календарь."

    creds = get_credentials(user_id)
    if not creds:
        return False, f"Не удалось получить учетные данные для пользователя {user_email}."

    service = build('calendar', 'v3', credentials=creds)

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        logger.info(f"Событие {event_id} удалено из календаря для {user_email}.")
        return True, f"Событие успешно удалено."
    except Exception as e:
        logger.error(f"Ошибка при удалении события {event_id} из календаря {user_email}: {e}")
        return False, f"Ошибка при удалении события {event_id}: {e}"
