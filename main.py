"""
main.py — точка входа в приложение.

Запускает Telegram-бота:
1. Инициализирует базу данных
2. Регистрирует обработчики команд и сообщений
3. Запускает polling (бот постоянно проверяет новые сообщения)

Запуск:
    python main.py
"""

# config импортируется первым — он настраивает логгирование для всего приложения
import config  # noqa: F401  (импорт нужен ради побочного эффекта — настройки логов)

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from database import init_db
from handlers import handle_document, handle_message, start


def main() -> None:
    """Инициализирует и запускает Telegram-бота."""
    # Создаём таблицы в базе данных (если они ещё не существуют)
    init_db()

    # Создаём приложение Telegram с нашим токеном
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики:
    # /start — сброс контекста и приветствие
    app.add_handler(CommandHandler("start", start))
    # Текстовые сообщения (кроме команд) — отправляем в DeepSeek API
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Документы (PDF, DOCX, TXT) — извлекаем текст и сохраняем
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Запускаем бота в режиме polling
    # Бот будет работать до нажатия Ctrl+C
    app.run_polling()


if __name__ == "__main__":
    main()
