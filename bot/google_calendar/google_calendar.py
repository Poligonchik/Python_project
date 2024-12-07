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


