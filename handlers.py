"""
handlers.py — обработчики сообщений Telegram-бота.

Содержит три обработчика:
- start()           — команда /start, сброс контекста
- handle_document() — загрузка и сохранение документов
- handle_message()  — обработка текстовых вопросов через DeepSeek API
"""

import asyncio
import json
import logging
from io import BytesIO

from openai import OpenAI
from telegram import Update
from telegram.ext import ContextTypes

import config
from database import (
    get_file_content,
    get_user_context,
    save_file_content,
    update_user_context,
)
from extractors import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_txt,
)

logger = logging.getLogger(__name__)

# Клиент DeepSeek API.
# Используем библиотеку openai с переопределённым base_url,
# потому что DeepSeek совместим с форматом OpenAI API.
_client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.BASE_URL)


# ──────────────────────────────────────────────
# Вспомогательная функция
# ──────────────────────────────────────────────

def _truncate_context(messages: list[dict]) -> list[dict]:
    """
    Обрезает историю диалога, если она превышает MAX_CONTEXT_SIZE байт.

    Всегда сохраняет первое сообщение (системный промпт) и
    оставляет последние MAX_CONTEXT_MESSAGES сообщений.

    Args:
        messages: Список сообщений в формате [{"role": ..., "content": ...}, ...]

    Returns:
        Укороченный (или исходный, если обрезка не нужна) список сообщений.
    """
    if len(json.dumps(messages)) > config.MAX_CONTEXT_SIZE:
        logger.warning("Контекст превышает %d байт — обрезка.", config.MAX_CONTEXT_SIZE)
        # Сохраняем системный промпт + последние N сообщений
        system_message = messages[:1]
        recent_messages = messages[-config.MAX_CONTEXT_MESSAGES:]
        return system_message + recent_messages

    return messages


# ──────────────────────────────────────────────
# Обработчики Telegram
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.

    Сбрасывает историю диалога пользователя и отправляет приветствие.
    """
    user_id = update.message.from_user.id
    update_user_context(user_id, [{"role": "system", "content": config.SYSTEM_PROMPT}])
    await update.message.reply_text(
        "Привет! Я AI-бот на базе DeepSeek.\n\n"
        "Отправь мне текстовый вопрос или документ (PDF, DOCX, TXT) — "
        "и я постараюсь помочь!"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик входящих документов.

    Скачивает файл, извлекает из него текст и сохраняет в базу данных.
    Поддерживаемые форматы: PDF, DOCX, TXT.
    Максимальный размер файла: 10 MB.
    """
    user_id = update.message.from_user.id
    document = update.message.document

    # Проверяем размер файла до скачивания
    if document.file_size > config.MAX_FILE_SIZE:
        await update.message.reply_text(
            "Файл слишком большой. Максимальный размер: 10 MB."
        )
        return

    # Скачиваем файл в память (не сохраняем на диск)
    tg_file = await context.bot.get_file(document.file_id)
    file_bytes = BytesIO()
    await tg_file.download_to_memory(file_bytes)
    file_bytes.seek(0)  # Перематываем указатель на начало перед чтением

    file_name = document.file_name.lower()

    try:
        # Выбираем нужный экстрактор по расширению файла
        if file_name.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        elif file_name.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
        elif file_name.endswith(".txt"):
            text = extract_text_from_txt(file_bytes)
        else:
            await update.message.reply_text(
                "Формат файла не поддерживается. "
                "Пожалуйста, отправьте файл в формате PDF, DOCX или TXT."
            )
            return

        save_file_content(user_id, file_name, text)
        await update.message.reply_text(
            f'Файл "{document.file_name}" успешно загружен и сохранён. '
            "Теперь вы можете задать вопрос по его содержимому."
        )

    except ValueError as e:
        # ValueError — ожидаемая ошибка (пустой файл, неверный формат)
        await update.message.reply_text(f"Ошибка при обработке файла: {e}")
    except Exception as e:
        # Непредвиденная ошибка — логируем подробности, пользователю показываем общее сообщение
        logger.error("Ошибка при обработке документа (user_id=%d): %s", user_id, e)
        await update.message.reply_text(
            "Произошла непредвиденная ошибка при обработке файла. "
            "Пожалуйста, попробуйте ещё раз."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик текстовых сообщений.

    Алгоритм работы:
    1. Получаем историю диалога пользователя из базы данных.
    2. Обрезаем историю, если она слишком большая.
    3. Добавляем тексты из загруженных файлов (если есть).
    4. Добавляем новое сообщение пользователя.
    5. Отправляем всё это в DeepSeek API.
    6. Сохраняем ответ в историю и отправляем пользователю.

    При ошибке API — повторяем попытку до MAX_RETRIES раз.
    """
    user_id = update.message.from_user.id
    user_message = update.message.text

    # Загружаем и при необходимости обрезаем историю диалога
    messages = _truncate_context(get_user_context(user_id))

    # Если у пользователя есть загруженные файлы — добавляем их содержимое в контекст
    file_contents = get_file_content(user_id)
    if file_contents:
        combined_files = " ".join(file_contents)
        messages.append({"role": "user", "content": f"Данные из файлов: {combined_files}"})

    # Добавляем текущее сообщение пользователя
    messages.append({"role": "user", "content": user_message})

    for attempt in range(config.MAX_RETRIES):
        try:
            # Отправляем запрос к DeepSeek API
            response = _client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False,
            )

            # Проверяем структуру ответа
            if not response.choices:
                raise ValueError("API вернул пустой список choices")

            answer = response.choices[0].message.content.strip()
            if not answer:
                raise ValueError("API вернул пустой текст ответа")

            # Сохраняем ответ бота в историю и обновляем базу данных
            messages.append({"role": "assistant", "content": answer})
            update_user_context(user_id, messages)

            # Telegram не позволяет отправлять сообщения длиннее 4096 символов —
            # разбиваем длинный ответ на части
            for i in range(0, len(answer), config.MAX_TELEGRAM_MESSAGE):
                chunk = answer[i : i + config.MAX_TELEGRAM_MESSAGE].strip()
                if chunk:
                    await update.message.reply_text(chunk)

            break  # Запрос прошёл успешно — выходим из цикла повторов

        except ValueError as e:
            # Проблема с содержимым ответа — повторная попытка не поможет
            logger.error("Ошибка валидации ответа (попытка %d): %s", attempt + 1, e)
            if attempt == config.MAX_RETRIES - 1:
                await update.message.reply_text(
                    "Произошла ошибка при обработке ответа. "
                    "Пожалуйста, попробуйте ещё раз."
                )

        except Exception as e:
            # Сетевая или серверная ошибка — имеет смысл повторить
            logger.error("Ошибка запроса к API (попытка %d): %s", attempt + 1, e)
            if attempt == config.MAX_RETRIES - 1:
                await update.message.reply_text(
                    "Временная ошибка API. Пожалуйста, попробуйте позже."
                )
            else:
                logger.warning(
                    "Повторная попытка %d/%d...", attempt + 2, config.MAX_RETRIES
                )
                # ВАЖНО: используем await asyncio.sleep(), а не time.sleep()!
                # time.sleep() заблокировал бы весь event loop — бот перестал бы
                # отвечать всем остальным пользователям на время ожидания.
                await asyncio.sleep(config.RETRY_DELAY)
