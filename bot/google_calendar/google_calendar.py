from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import os
import pickle
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            creds.refresh(Request())              # Если вдруг нет, то обновляем
            save_credentials(user_id, creds)      # и сохраняем
        return creds
    else:
        logger.warning(f"Токен отсутствует для пользователя {user_id}")
    return None

# Сохраняем новый токен
def save_credentials(user_id, creds):
    token_path = f"bot/token_{user_id}.pickle"
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)   # берет creds и записывает в token

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


