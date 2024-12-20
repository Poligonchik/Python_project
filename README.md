# Python_project
# Телеграм-бот для создания встреч в Google Календаре  

 📋 Описание  
Этот бот позволяет создавать встречи в Google Календаре через чат в Телеграме. Введите основные данные о встрече, и бот автоматически создаст событие с нужными параметрами в гугл Календаре.  

---

🚀 Установка и настройка  

1. Клонирование репозитория  
git clone <URL репозитория>  
cd <папка проекта>  

 2. Установка библиотек
pip install -r requirements.txt  

3. Получение учетных данных Google API
1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/).  
2. Создайте новый проект.  
3. Включите Google Calendar API.
4. Перейдите в credentials и настройте OAuth 2.0
5. Нажмите на Download OAuth client и скачайте credentials.json и поместите его в папку bot.


 ▶️ Запуск бота  
python -m bot.main
или запустить файл main.py в проекте


🛠 Функционал 
бот умеет:
1. Подключаться к Гугл календарю пользователя и создавать там встречи
  1.1 Создать встречу с заданными параметрами (Название, дата, описание, участники)
  1.2 Создать встречу и установить автоматически время удобное всем участникам
2. Хранить и редактировать данные пользователя
  2.1 Имя
  2.2 Привязанный календарь
  2.3 Время в которое не стоит беспокоить пользователя
  2.4 Черный список
3. Собирать статистикиу о встречах и выдавать ее в виде графиков
   
Пример работы с ботом. 
1. Пройти авторизацию (подключение гугл календаря)
2. Внести данные пользователя
3. Добавить встречу
   

📂 Структура проекта  

# Python_project
# Телеграм-бот для создания встреч в Google Календаре  

 📋 Описание  
Этот бот позволяет создавать встречи в Google Календаре через чат в Телеграме. Введите основные данные о встрече, и бот автоматически создаст событие с нужными параметрами в гугл Календаре.  

---

🚀 Установка и настройка  

1. Клонирование репозитория  
git clone <URL репозитория>  
cd <папка проекта>  

 2. Установка библиотек
pip install -r requirements.txt  

3. Получение учетных данных Google API
1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/).  
2. Создайте новый проект.  
3. Включите Google Calendar API.
4. Перейдите в credentials и настройте OAuth 2.0
5. Нажмите на Download OAuth client и скачайте credentials.json и поместите его в папку bot.


 ▶️ Запуск бота  
python -m bot.main
или запустить файл main.py в проекте


🛠 Функционал 
бот умеет:
1. Подключаться к Гугл календарю пользователя и создавать там встречи
  1.1 Создать встречу с заданными параметрами (Название, дата, описание, участники)
  1.2 Создать встречу и установить автоматически время удобное всем участникам
2. Хранить и редактировать данные пользователя
  2.1 Имя
  2.2 Привязанный календарь
  2.3 Время в которое не стоит беспокоить пользователя
  2.4 Черный список
3. Собирать статистикиу о встречах и выдавать ее в виде графиков
   
Пример работы с ботом. 
1. Пройти авторизацию (подключение гугл календаря)
2. Внести данные пользователя
3. Добавить встречу
   

📂 Структура проекта  

<br>│
<br>├── .venv/                         # Виртуальное окружение
<br>│
<br>├── bot/                           # Основная папка с ботом
<br>│   ├── databases/                 # База данных проекта
<br>│   │   ├── black_list.db          # База данных черного списка
<br>│   │   ├── meet.db                # База данных встреч
<br>│   │   ├── sleep_time.db          # База данных с временем сна
<br>│   │   ├── statistic.db           # База данных с статистика
<br>│   │   ├── team.db                # База данных с пользователями на встречах
<br>│   │   └── users.db               # База данных пользователей
<br>│   │
<br>│   ├── databases_methods/         # Скрипты для работы с базами данных
<br>│   │   ├── db_black_list.py       # Логика работы с черным списком
<br>│   │   ├── db_meet.py             # Логика работы с встречами
<br>│   │   ├── db_sleep_time.py       # Логика работы с временем сна
<br>│   │   ├── db_statistic.py        # Логика работы со статистикой
<br>│   │   ├── db_team.py             # Логика работы с командой
<br>│   │   ├── db_user.py             # Логика работы с пользователями
<br>│   │   └── delete_all_db.py       # Скрипт для очистки всех баз данных
<br>│   │
<br>│   ├── google_calendar/           # Логика работы с Google Календарем
<br>│   │   ├── google_calendar.py     # Основной файл для работы с Google Календарем
<br>│   │   └── handlers_calendar.py   # Обработчик URL и кода OAuth
<br>│   │
<br>│   ├── edit_command.py            # Работа с кнопкой /edit (редактирование пользовательских данных)
<br>│   ├── help_handler.py            # Работа с кнопкой /help (список команд)
<br>│   ├── main.py                    # Главный файл бота
<br>│   ├── calendari.json             # Файл для настройки Google API
<br>│   ├── constants.py               # Этапы диалога
<br>│   ├── meeting_plan               # Создание встречи и описания
<br>│   └── token_1.pickle             # Токен авторизации
<br>│
<br>├── .gitignore                     # Игнорируемые файлы для Git
<br>├── README.md                      # Документация проекта
<br>├── requirements.txt               # Библиотеки используемые в проекте
<br>├── notes.txt                      # Примечания для разработчиков, когда проект будет готов, файл будет удален
<br>└── .env                           # Переменные окружения
