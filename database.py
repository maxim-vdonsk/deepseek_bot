"""
database.py — работа с базой данных SQLite.

Содержит:
- Инициализацию таблиц
- Функции для сохранения и получения истории диалога
- Функции для сохранения и получения содержимого загруженных файлов
"""

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Создаём соединение с SQLite.
# check_same_thread=False нужен, потому что бот использует asyncio
# и обращается к базе из разных потоков выполнения.
_conn = sqlite3.connect("bot_context.db", check_same_thread=False)
_cursor = _conn.cursor()


def init_db() -> None:
    """Создаёт таблицы в базе данных, если они ещё не существуют."""
    # Таблица для хранения истории диалога каждого пользователя
    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_context (
            user_id INTEGER PRIMARY KEY,
            context TEXT
        )
    """)

    # Таблица для хранения текста из загруженных файлов
    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_files (
            user_id   INTEGER,
            file_name TEXT,
            file_content TEXT,
            PRIMARY KEY (user_id, file_name)
        )
    """)

    _conn.commit()


def get_user_context(user_id: int) -> list[dict]:
    """
    Возвращает историю диалога пользователя из базы данных.

    Если записи нет или она повреждена — возвращает начальный системный промпт.
    """
    # Импортируем здесь, чтобы избежать циклических зависимостей
    from config import SYSTEM_PROMPT

    _cursor.execute(
        "SELECT context FROM user_context WHERE user_id = ?", (user_id,)
    )
    result = _cursor.fetchone()

    if result and result[0].strip():
        try:
            return json.loads(result[0])
        except json.JSONDecodeError:
            logger.error("Ошибка декодирования JSON для user_id %d", user_id)

    # Возвращаем пустой контекст с системным промптом
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def update_user_context(user_id: int, messages: list[dict]) -> None:
    """Сохраняет (или обновляет) историю диалога пользователя в базе данных."""
    _cursor.execute(
        """
        INSERT OR REPLACE INTO user_context (user_id, context)
        VALUES (?, ?)
        """,
        (user_id, json.dumps(messages)),
    )
    _conn.commit()


def save_file_content(user_id: int, file_name: str, file_content: str) -> None:
    """Сохраняет текст, извлечённый из файла, в базе данных."""
    _cursor.execute(
        """
        INSERT OR REPLACE INTO user_files (user_id, file_name, file_content)
        VALUES (?, ?, ?)
        """,
        (user_id, file_name, file_content),
    )
    _conn.commit()


def get_file_content(user_id: int) -> list[str]:
    """Возвращает список текстов всех загруженных файлов пользователя."""
    _cursor.execute(
        "SELECT file_content FROM user_files WHERE user_id = ?", (user_id,)
    )
    return [row[0] for row in _cursor.fetchall()]
