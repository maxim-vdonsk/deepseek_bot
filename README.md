**Telegram Bot с поддержкой AI и обработкой документов**

*Описание*

Этот проект представляет собой Telegram-бота, который использует API DeepSeek для взаимодействия с пользователем. 
Бот может отвечать на текстовые запросы, а также обрабатывать документы в форматах PDF, DOCX и TXT. 
Он сохраняет контекст разговора и данные из загруженных файлов в базе данных SQLite, чтобы использовать их при последующих запросах.

***Функциональность :***

**Обработка текстовых запросов :**

- Пользователь может отправлять текстовые сообщения, и бот будет отвечать с помощью модели DeepSeek.
- Контекст разговора хранится в базе данных для обеспечения непрерывного диалога.

**Загрузка и обработка документов :**
  
- Поддерживаются форматы: PDF, DOCX, TXT.
- Максимальный размер файла: 10 MB.
- Текст из загруженных документов автоматически извлекается и сохраняется в базу данных.
- Данные из документов могут быть использованы в качестве дополнительного контекста для ответов.
  
**Ретраи и обработка ошибок :**

- Реализована система повторных попыток при временных ошибках API.
- Логирование ошибок для упрощения отладки.
  
**Ограничение размера контекста :**

- Чтобы не превышать лимиты API, контекст автоматически обрезается до 32 КБ.

**Логирование :**

- Все события записываются в файл bot.log для анализа и отслеживания работы бота.
  
***Требования***

Python 3.9+
- pip (для установки зависимостей)
- База данных SQLite (автоматически создается при запуске)
- API ключи:
  - TELEGRAM_BOT_TOKEN: токен Telegram-бота.
  - DEEPSEEK_API_KEY: ключ API для доступа к моделям DeepSeek.
  - BASE_URL: URL для API DeepSeek.
    
***Установка и запуск***

1. Клонирование репозитория
   
```bash
git clone https://github.com/maxim-vdonsk/deepseek_bot.git
cd deepseek_bot
```
2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate
```
3. Установка зависимостей

```bash
pip install -r requirements.txt
```
4. Настройка переменных окружения

Создайте файл .env в корне проекта и добавьте следующие переменные:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
BASE_URL=https://api.deepseek.ai/v1
```
*Примечание : Замените значения на свои реальные токены и URL.*

5. Запуск бота

```bash
python bot.py
Бот начнет работу и будет доступен в Telegram.
```
***Пример использования*** 

- Отправьте команду /start, чтобы начать диалог.
- Отправьте текстовый запрос или документ (PDF, DOCX, TXT).
- Бот обработает запрос и предоставит ответ.
  
***Структура проекта***
  
- main.py: Основной файл бота.
- requirements.txt: Список зависимостей.
- .env: Файл с переменными окружения.
- bot.log: Файл логов.
- bot_context.db База данных SQLite
  

Лицензия
Данный проект распространяется под лицензией MIT. Подробнее см. файл LICENSE .
