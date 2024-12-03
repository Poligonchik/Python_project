from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_event():
    # Используем токен из файла token.json
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    # Основной календарь (можно указать ID другого календаря)
    calendar_id = 'primary'

    # Параметры события
    event = {
        'summary': 'Тестовое событие',
        'description': 'Описание тестового события',
        'start': {
            'dateTime': '2024-12-05T10:00:00+03:00',
            'timeZone': 'Europe/Moscow',
        },
        'end': {
            'dateTime': '2024-12-05T11:00:00+03:00',
            'timeZone': 'Europe/Moscow',
        },
    }

    try:
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Событие успешно создано: {event_result.get('htmlLink')}")
    except Exception as e:
        print(f"Ошибка при создании события: {e}")

# Запуск создания события
create_event()
