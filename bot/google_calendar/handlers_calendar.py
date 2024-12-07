from telegram import Update
from telegram.ext import ContextTypes
from bot.databases_methods.db_user import get_user_by_link, get_user_id_by_telegram_id, edit_user_calendar_id
from bot.google_calendar.google_calendar import extract_calendar_id, get_credentials, save_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from bot.constants import CHOICE, AUTH
import logging

logger = logging.getLogger(__name__)
# Области доступа
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Обработка ссылки на календарь и привязка к пользователю
async def handle_calendar_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    url = "https://calendar.google.com/calendar/u/0/r?cid=" + update.message.text.strip()
    calendar_id = extract_calendar_id(url)
    if not calendar_id:
        await update.message.reply_text(
            "Не удалось распознать Calendar ID. Пожалуйста, отправьте корректную почту, к которой привзяна Google Календарь."
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
