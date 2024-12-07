from google_auth_oauthlib.flow import InstalledAppFlow

# Области доступа (для работы с Google Calendar)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def generate_token():
    # Укажите путь к вашему credentials.json
    flow = InstalledAppFlow.from_client_secrets_file('calendari.json', SCOPES)
    creds = flow.run_local_server(port=0)  # Локальный сервер для авторизации
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Файл token.json успешно создан!")

# Запуск генерации токена
generate_token()
