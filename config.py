"""
config.py — конфигурация бота.

Здесь хранятся все настройки: переменные окружения, константы и логгирование.
Этот файл должен импортироваться ПЕРВЫМ, потому что он настраивает логгирование
для всего приложения.
"""

import logging
import os

from dotenv import load_dotenv

# Загружаем переменные из файла .env в окружение
load_dotenv()

# ──────────────────────────────────────────────
# Секретные ключи (берутся из .env файла)
# ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY")
BASE_URL: str = os.getenv("BASE_URL", "https://api.deepseek.com/v1")

# Проверяем, что обязательные переменные заданы
if not TELEGRAM_BOT_TOKEN or not DEEPSEEK_API_KEY:
    raise ValueError(
        "Не установлены обязательные переменные окружения: "
        "TELEGRAM_BOT_TOKEN или DEEPSEEK_API_KEY. "
        "Убедитесь, что файл .env существует и заполнен."
    )

# ──────────────────────────────────────────────
# Константы приложения
# ──────────────────────────────────────────────
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # Максимальный размер загружаемого файла — 10 MB
MAX_CONTEXT_SIZE: int = 32 * 1024      # Максимальный размер истории чата — 32 KB
MAX_CONTEXT_MESSAGES: int = 10         # Сколько последних сообщений оставлять при обрезке
MAX_TELEGRAM_MESSAGE: int = 4096       # Лимит символов в одном сообщении Telegram
MAX_RETRIES: int = 5                   # Максимум повторных попыток при ошибке API
RETRY_DELAY: int = 3                   # Задержка между попытками (в секундах)

# Системный промпт — инструкция для AI-модели
SYSTEM_PROMPT: str = "You are a helpful assistant."

# ──────────────────────────────────────────────
# Настройка логгирования
# ──────────────────────────────────────────────
# Формат: время - имя модуля - уровень - сообщение
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
    encoding="utf-8",
)
